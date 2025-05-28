import logging
from time import sleep
from datetime import datetime, timezone

from django.db.models import F, Func, Value, JSONField
from django.db.models.functions import JSONObject
from django.contrib.postgres.aggregates import JSONBAgg

from fyle_accounting_mappings.models import ExpenseAttribute
from fyle_integrations_platform_connector import PlatformConnector
from fyle.platform.exceptions import InvalidTokenError as FyleInvalidTokenError
from fyle_intacct_api.utils import invalidate_sage_intacct_credentials

from sageintacctsdk.exceptions import (
    InvalidTokenError,
    NoPrivilegeError,
    SageIntacctSDKError
)

from apps.mappings.models import ImportLog
from apps.sage_intacct.models import CostCode, CostType
from apps.fyle.models import DependentFieldSetting
from apps.fyle.helpers import connect_to_platform
from apps.mappings.helpers import prepend_code_to_name
from apps.mappings.tasks import sync_sage_intacct_attributes
from apps.mappings.exceptions import handle_import_exceptions
from apps.workspaces.models import Configuration, SageIntacctCredential

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def construct_custom_field_placeholder(source_placeholder: str, fyle_attribute: str, existing_attribute: dict) -> str:
    """
    Construct the placeholder for the custom field
    :param source_placeholder: Placeholder filled by user in the custom field form
    :param fyle_attribute: Fyle attribute for which the custom field is being created
    :param existing_attribute: Existing attribute in Fyle
    :return: Constructed placeholder
    """
    new_placeholder = None
    placeholder = None

    if existing_attribute:
        placeholder = existing_attribute['placeholder'] if 'placeholder' in existing_attribute else None

    # Here is the explanation of what's happening in the if-else ladder below
    # source_field is the field that's save in mapping settings, this field user may or may not fill in the custom field form
    # placeholder is the field that's saved in the detail column of destination attributes
    # fyle_attribute is what we're constructing when both of these fields would not be available

    if not (source_placeholder or placeholder):
        # If source_placeholder and placeholder are both None, then we're creating adding a self constructed placeholder
        new_placeholder = 'Select {0}'.format(fyle_attribute)
    elif not source_placeholder and placeholder:
        # If source_placeholder is None but placeholder is not, then we're choosing same place holder as 1 in detail section
        new_placeholder = placeholder
    elif source_placeholder and not placeholder:
        # If source_placeholder is not None but placeholder is None, then we're choosing the placeholder as filled by user in form
        new_placeholder = source_placeholder
    else:
        # Else, we're choosing the placeholder as filled by user in form or None
        new_placeholder = source_placeholder

    return new_placeholder


@handle_import_exceptions
def post_dependent_cost_code(import_log: ImportLog, dependent_field_setting: DependentFieldSetting, platform: PlatformConnector, filters: dict, is_enabled: bool = True) -> tuple:
    """
    Post dependent cost code to Fyle
    :param import_log: Import log object
    :param dependent_field_setting: Dependent field setting object
    :param platform: Platform connector object
    :param filters: Filters to apply on the cost codes
    :param is_enabled: Flag to enable/disable the cost code
    :return: Tuple of posted cost codes and is_errored flag
    """
    configuration = Configuration.objects.filter(workspace_id=dependent_field_setting.workspace_id).first()

    last_successful_run_at = datetime.now(timezone.utc)
    use_job_code_in_naming = 'PROJECT' in configuration.import_code_fields
    use_cost_code_in_naming = 'COST_CODE' in configuration.import_code_fields

    posted_cost_codes = set()
    total_batches = 0
    processed_batches = 0
    is_errored = False
    projects_batch = []

    """
        Structure of the query output:
        [
            {
                "project_name": "Project A",
                "project_id": "1",
                "cost_codes": [
                    {
                        "cost_code_name": "Task 1",
                        "cost_code_code": "101"
                    },
                    {
                        "cost_code_name": "Task 2",
                        "cost_code_code": "102"
                    }
                ]
            }
        ]

        SQL Query:
        SELECT
            project_name AS project_name,
            project_id AS project_id,
            JSON_AGG(
                JSON_BUILD_OBJECT(
                    'cost_code_name', value,
                    'cost_code_code', destination_id
                )
            ) AS cost_codes
        FROM
            cost_codes
        WHERE
            workspace_id = 1
        GROUP BY
            project_name,
            project_id;
    """
    if not dependent_field_setting.is_cost_type_import_enabled:
        projects_batch = (
            CostCode.objects.filter(**filters)
            .values('project_name', 'project_id')
            .annotate(
                cost_codes=JSONBAgg(
                    JSONObject(
                        cost_code_name=F('task_name'),  # value -> task_name
                        cost_code_code=F('task_id')  # destination_id -> task_id
                    ),
                    output_field=JSONField(),
                    distinct=True
                )
            )
        )
    else:
        projects_batch = (
            CostType.objects.filter(**filters)
            .values('project_name', 'project_id')
            .annotate(
                cost_codes=JSONBAgg(
                    Func(
                        Value('cost_code_name'), F('task_name'),
                        Value('cost_code_code'), F('task_id'),
                        function='jsonb_build_object'
                    ),
                    output_field=JSONField(),
                    distinct=True
                )
            )
        )

    existing_projects_in_fyle = set(
        ExpenseAttribute.objects.filter(
            workspace_id=dependent_field_setting.workspace_id,
            attribute_type='PROJECT',
            value__in=[
                prepend_code_to_name(use_job_code_in_naming, project['project_name'], project['project_id'])
                for project in projects_batch
            ],
            active=True
        ).values_list('value', flat=True)
    )

    logger.info(f'Posting Cost Codes | WORKSPACE_ID: {dependent_field_setting.workspace_id} | Existing Projects in Fyle COUNT: {len(existing_projects_in_fyle)}')

    for project in projects_batch:
        payload = []
        cost_code_names = set()
        project_name = prepend_code_to_name(use_job_code_in_naming, project['project_name'], project['project_id'])

        if project_name in existing_projects_in_fyle:
            for cost_code in project['cost_codes']:
                cost_code_name = prepend_code_to_name(prepend_code_in_name=use_cost_code_in_naming, value=cost_code['cost_code_name'], code=cost_code['cost_code_code'])
                payload.append({
                    'parent_expense_field_id': dependent_field_setting.project_field_id,
                    'parent_expense_field_value': project_name,
                    'expense_field_id': dependent_field_setting.cost_code_field_id,
                    'expense_field_value': cost_code_name,
                    'is_enabled': is_enabled
                })
                cost_code_names.add(cost_code['cost_code_name'])

            if payload:
                sleep(0.2)
                try:
                    total_batches += 1
                    platform.dependent_fields.bulk_post_dependent_expense_field_values(payload)
                    posted_cost_codes.update(cost_code_names)
                    processed_batches += 1
                except Exception as exception:
                    is_errored = True
                    logger.error(f'Exception while posting dependent cost code | Error: {exception} | Payload: {payload}')

    if is_errored or import_log.status != 'IN_PROGRESS':
        import_log.status = 'PARTIALLY_FAILED'
    else:
        import_log.status = 'COMPLETE'
        import_log.error_log = []
        import_log.last_successful_run_at = last_successful_run_at

    import_log.total_batches_count = total_batches
    import_log.processed_batches_count = processed_batches
    import_log.save()

    return posted_cost_codes, is_errored


@handle_import_exceptions
def post_dependent_cost_type(import_log: ImportLog, dependent_field_setting: DependentFieldSetting, platform: PlatformConnector, filters: dict) -> bool:
    """
    Post dependent cost type to Fyle
    :param import_log: Import log object
    :param dependent_field_setting: Dependent field setting object
    :param platform: Platform connector object
    :param filters: Filters to apply on the cost types
    :return: is_errored flag
    """
    configuration = Configuration.objects.filter(workspace_id=dependent_field_setting.workspace_id).first()

    last_successful_run_at = datetime.now(timezone.utc)
    use_cost_code_in_naming = 'COST_CODE' in configuration.import_code_fields
    use_cost_type_code_in_naming = 'COST_TYPE' in configuration.import_code_fields

    total_batches = 0
    processed_batches = 0
    is_errored = False

    cost_types_batch = (
        CostType.objects.filter(**filters)
        .values('task_name', 'task_id')
        .annotate(
            cost_types=JSONBAgg(
                Func(
                    Value('cost_type_name'), F('name'),
                    Value('cost_type_code'), F('cost_type_id'),
                    function='jsonb_build_object'
                ),
                output_field=JSONField(),
                distinct=True
            )
        )
    )

    logger.info(f'Posting Cost Types | WORKSPACE_ID: {dependent_field_setting.workspace_id} | Existing Cost Code in Fyle COUNT: {len(cost_types_batch)}')

    for cost_types in cost_types_batch:
        payload = []
        cost_code_name = prepend_code_to_name(use_cost_code_in_naming, cost_types['task_name'], cost_types['task_id'])

        for cost_type in cost_types['cost_types']:
            cost_type_name = prepend_code_to_name(use_cost_type_code_in_naming, cost_type['cost_type_name'], cost_type['cost_type_code'])
            payload.append({
                'parent_expense_field_id': dependent_field_setting.cost_code_field_id,
                'parent_expense_field_value': cost_code_name,
                'expense_field_id': dependent_field_setting.cost_type_field_id,
                'expense_field_value': cost_type_name,
                'is_enabled': True
            })

        if payload:
            sleep(0.2)
            try:
                total_batches += 1
                platform.dependent_fields.bulk_post_dependent_expense_field_values(payload)
                CostType.objects.filter(task_name=cost_types['task_name'], task_id=cost_types['task_id'], workspace_id=dependent_field_setting.workspace_id).update(is_imported=True, updated_at=datetime.now(timezone.utc))
                processed_batches += 1
            except Exception as exception:
                is_errored = True
                logger.error(f'Exception while posting dependent cost type | Error: {exception} | Payload: {payload}')

    if is_errored or import_log.status != 'IN_PROGRESS':
        import_log.status = 'PARTIALLY_FAILED'
    else:
        import_log.status = 'COMPLETE'
        import_log.error_log = []
        import_log.last_successful_run_at = last_successful_run_at

    import_log.total_batches_count = total_batches
    import_log.processed_batches_count = processed_batches
    import_log.save()

    return is_errored


def post_dependent_cost_code_standalone(workspace_id: int, dependent_field_setting: DependentFieldSetting, platform: PlatformConnector, cost_code_import_log: ImportLog) -> None:
    """
    Post dependent cost code to Fyle
    :param workspace_id: Workspace ID
    :param dependent_field_setting: Dependent field setting object
    :param platform: Platform connector object
    :param cost_code_import_log: Cost code import log object
    :return: None
    """
    filters = {
        'workspace_id': workspace_id
    }

    if dependent_field_setting.last_successful_import_at:
        filters['updated_at__gte'] = dependent_field_setting.last_successful_import_at

    _, is_errored = post_dependent_cost_code(cost_code_import_log, dependent_field_setting, platform, filters)

    if not is_errored and cost_code_import_log.processed_batches_count == cost_code_import_log.total_batches_count:
        DependentFieldSetting.objects.filter(workspace_id=workspace_id).update(last_successful_import_at=datetime.now())


def post_dependent_expense_field_values(workspace_id: int, dependent_field_setting: DependentFieldSetting, platform: PlatformConnector = None, cost_code_import_log: ImportLog = None, cost_type_import_log: ImportLog = None) -> None:
    """
    Post dependent expense field values to Fyle
    :param workspace_id: Workspace ID
    :param dependent_field_setting: Dependent field setting object
    :param platform: Platform connector object
    :param cost_code_import_log: Cost code import log object
    :param cost_type_import_log: Cost type import log object
    :return: None
    """
    if not platform:
        platform = connect_to_platform(workspace_id)

    filters = {
        'workspace_id': workspace_id
    }

    if dependent_field_setting.last_successful_import_at:
        filters['updated_at__gte'] = dependent_field_setting.last_successful_import_at
    else:
        filters['is_imported'] = False

    posted_cost_types, is_cost_code_errored = post_dependent_cost_code(cost_code_import_log, dependent_field_setting, platform, filters)
    if posted_cost_types:
        filters['is_imported'] = False
        filters['task_name__in'] = list(set(posted_cost_types))

    if cost_code_import_log.status in ['FAILED', 'FATAL']:
        cost_type_import_log.status = 'FAILED'
        cost_type_import_log.error_log = {'message': 'Importing COST_CODE failed'}
        cost_type_import_log.save()
        return
    else:
        is_cost_type_errored = post_dependent_cost_type(cost_type_import_log, dependent_field_setting, platform, filters)
        if not is_cost_type_errored and not is_cost_code_errored and (
            cost_type_import_log.processed_batches_count == cost_type_import_log.total_batches_count
            and cost_code_import_log.processed_batches_count == cost_code_import_log.total_batches_count
        ):
            DependentFieldSetting.objects.filter(workspace_id=workspace_id).update(last_successful_import_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))


def import_dependent_fields_to_fyle(workspace_id: str) -> None:
    """
    Import dependent fields to Fyle
    :param workspace_id: Workspace ID
    :return: None
    """
    dependent_field = DependentFieldSetting.objects.get(workspace_id=workspace_id)

    cost_code_import_log = ImportLog.update_or_create(attribute_type='COST_CODE', workspace_id=workspace_id)
    cost_type_import_log = None

    if dependent_field.is_cost_type_import_enabled:
        cost_type_import_log = ImportLog.update_or_create(attribute_type='COST_TYPE', workspace_id=workspace_id)

    exception = None
    try:
        platform = connect_to_platform(workspace_id)
        if dependent_field.is_cost_type_import_enabled:
            sync_sage_intacct_attributes('COST_TYPE', workspace_id)
            if cost_code_import_log.status == 'IN_PROGRESS' and cost_type_import_log.status == 'IN_PROGRESS':
                post_dependent_expense_field_values(workspace_id, dependent_field, platform, cost_code_import_log, cost_type_import_log)
            else:
                logger.error('Importing dependent fields to Fyle failed | CONTENT: {{WORKSPACE_ID: {}}}'.format(workspace_id))
        else:
            sync_sage_intacct_attributes('COST_CODE', workspace_id)
            if cost_code_import_log.status == 'IN_PROGRESS':
                post_dependent_cost_code_standalone(workspace_id=workspace_id, dependent_field_setting=dependent_field, platform=platform, cost_code_import_log=cost_code_import_log)
            else:
                logger.error('Importing dependent fields to Fyle failed | CONTENT: {{WORKSPACE_ID: {}}}'.format(workspace_id))
    except SageIntacctCredential.DoesNotExist:
        exception = "Sage Intacct credentials does not exist workspace_id - {0}".format(workspace_id)
        logger.info('Sage Intacct credentials does not exist workspace_id - %s', workspace_id)
    except InvalidTokenError:
        invalidate_sage_intacct_credentials(workspace_id)
        exception = "Invalid Sage Intacct Token Error for workspace_id - {0}".format(workspace_id)
        logger.info('Invalid Sage Intacct Token Error for workspace_id - %s', workspace_id)
    except NoPrivilegeError:
        exception = "Insufficient permission to access the requested module"
        logger.info('Insufficient permission to access the requested module - %s', workspace_id)
    except FyleInvalidTokenError:
        exception = "Invalid Token or Fyle credentials does not exist"
        logger.info('Invalid Token or Fyle credentials does not exist - %s', workspace_id)
    except SageIntacctSDKError as e:
        exception = "Sage Intacct SDK Error"
        logger.info('Sage Intacct SDK Error - %s', e)
    except Exception as e:
        exception = e.__str__()
        logger.error('Exception while importing dependent fields to fyle - %s', exception)
    finally:
        if cost_type_import_log and cost_type_import_log.status == 'IN_PROGRESS':
            cost_type_import_log.status = 'FAILED'
            cost_type_import_log.error_log = exception
            cost_type_import_log.save()

        if cost_code_import_log and cost_code_import_log.status == 'IN_PROGRESS':
            cost_code_import_log.status = 'FAILED'
            cost_code_import_log.error_log = exception
            cost_code_import_log.save()


def create_dependent_custom_field_in_fyle(workspace_id: int, fyle_attribute_type: str, platform: PlatformConnector, parent_field_id: str, source_placeholder: str = None, cost_type_id: int = None, is_enabled: bool = True) -> dict:
    """
    Create dependent custom field in Fyle
    :param workspace_id: Workspace ID
    :param fyle_attribute_type: Fyle attribute type
    :param platform: Platform connector object
    :param parent_field_id: Parent field ID
    :param source_placeholder: Placeholder filled by user in the custom field form
    :return: Created custom field
    """
    existing_attribute = ExpenseAttribute.objects.filter(
        attribute_type=fyle_attribute_type,
        workspace_id=workspace_id
    ).values_list('detail', flat=True).first()

    placeholder = construct_custom_field_placeholder(source_placeholder, fyle_attribute_type, existing_attribute)

    expense_custom_field_payload = {
        'field_name': fyle_attribute_type,
        'column_name': fyle_attribute_type,
        'type': 'DEPENDENT_SELECT',
        'is_custom': True,
        'is_enabled': is_enabled,
        'is_mandatory': False,
        'placeholder': placeholder,
        'options': [],
        'parent_field_id': parent_field_id,
        'code': None
    }

    if cost_type_id:
        expense_custom_field_payload['id'] = cost_type_id

    return platform.expense_custom_fields.post(expense_custom_field_payload)


def update_and_disable_cost_code(workspace_id: int, cost_codes_to_disable: dict, platform: PlatformConnector, use_code_in_naming: bool) -> None:
    """
    Update the job_name in CostType and disable the old cost code in Fyle
    :param workspace_id: Workspace ID
    :param cost_codes_to_disable: Cost codes to disable
    :param platform: Platform connector object
    :param use_code_in_naming: Flag to use code in naming
    :return: None
    """
    dependent_field_setting = DependentFieldSetting.objects.filter(is_import_enabled=True, workspace_id=workspace_id).first()

    if dependent_field_setting:
        if dependent_field_setting.is_cost_type_import_enabled:
            disable_and_post_cost_code_from_cost_type_table(workspace_id, cost_codes_to_disable, platform, dependent_field_setting)
        else:
            disable_and_post_cost_code_from_cost_code_table(workspace_id, cost_codes_to_disable, platform, dependent_field_setting)


def disable_and_post_cost_code_from_cost_type_table(workspace_id: int, cost_codes_to_disable: dict, platform: PlatformConnector, dependent_field_setting: DependentFieldSetting) -> None:
    """
    Disable and post cost codes from cost type table
    :param workspace_id: Workspace ID
    :param cost_codes_to_disable: Cost codes to disable
    :param platform: Platform connector object
    :param dependent_field_setting: Dependent field setting object
    :return: None
    """
    filters = {
        'project_id__in': list(cost_codes_to_disable.keys()),
        'workspace_id': workspace_id
    }

    cost_code_import_log = ImportLog.update_or_create('COST_CODE', workspace_id)
    # This call will disable the cost codes in Fyle that has old project name
    posted_cost_codes, _ = post_dependent_cost_code(cost_code_import_log, dependent_field_setting, platform, filters, is_enabled=False)

    logger.info(f"Disabled Cost Codes in Fyle | WORKSPACE_ID: {workspace_id} | COUNT: {len(posted_cost_codes)}")

    BATCH_SIZE = 500

    for _, value in cost_codes_to_disable.items():
        cost_types_queryset = CostType.objects.filter(
            workspace_id=workspace_id,
            project_id=value['code']
        ).exclude(project_name=value['updated_value'], project_id=value['updated_code'])
        bulk_update_payload = []

        for cost_type in cost_types_queryset.iterator(chunk_size=BATCH_SIZE):
            cost_type.project_id = value['updated_code']
            cost_type.project_name = value['updated_value']
            # updating the updated_at, we'll post the COST_CODE to Fyle & not COST_TYPE # noqa
            cost_type.updated_at = datetime.now(timezone.utc)
            bulk_update_payload.append(cost_type)

            if len(bulk_update_payload) >= BATCH_SIZE:
                logger.info(f"Updating Cost Types | WORKSPACE_ID: {workspace_id} | COUNT: {len(bulk_update_payload)}")
                CostType.objects.bulk_update(bulk_update_payload, ['project_name', 'project_id', 'updated_at'], batch_size=50)
                bulk_update_payload = []

        # Final update for any remaining objects in the last batch
        if bulk_update_payload:
            logger.info(f"Updating Cost Types | WORKSPACE_ID: {workspace_id} | COUNT: {len(bulk_update_payload)}")
            CostType.objects.bulk_update(bulk_update_payload, ['project_name', 'project_id', 'updated_at'], batch_size=50)


def disable_and_post_cost_code_from_cost_code_table(workspace_id: int, cost_codes_to_disable: dict, platform: PlatformConnector, dependent_field_setting: DependentFieldSetting) -> None:
    """
    Disable and post cost codes from cost code table
    :param workspace_id: Workspace ID
    :param cost_codes_to_disable: Cost codes to disable
    :param platform: Platform connector object
    :param dependent_field_setting: Dependent field setting object
    :return: None
    """
    filters = {
        'project_id__in': list(cost_codes_to_disable.keys()),
        'workspace_id': workspace_id
    }
    cost_code_import_log = ImportLog.update_or_create('COST_CODE', workspace_id)
    # This call will disable the cost codes in Fyle that has old project name
    posted_cost_codes, _ = post_dependent_cost_code(cost_code_import_log, dependent_field_setting, platform, filters, is_enabled=False)

    logger.info(f"Disabled Cost Codes in Fyle | WORKSPACE_ID: {workspace_id} | COUNT: {len(posted_cost_codes)}")

    BATCH_SIZE = 500

    for _, value in cost_codes_to_disable.items():
        cost_codes_queryset = CostCode.objects.filter(
            workspace_id=workspace_id,
            project_id=value['code']
        ).exclude(project_name=value['updated_value'], project_id=value['updated_code'])

        bulk_update_payload = []

        for cost_code in cost_codes_queryset.iterator(chunk_size=BATCH_SIZE):
            cost_code.project_id = value['updated_code']
            cost_code.project_name = value['updated_value']

            # updating the updated_at, we'll post the COST_CODE to Fyle & not COST_TYPE # noqa
            cost_code.updated_at = datetime.now(timezone.utc)
            bulk_update_payload.append(cost_code)

            if len(bulk_update_payload) >= BATCH_SIZE:
                logger.info(f"Updating Cost Codes | WORKSPACE_ID: {workspace_id} | COUNT: {len(bulk_update_payload)}")
                CostCode.objects.bulk_update(bulk_update_payload, ['project_id', 'project_name', 'updated_at'], batch_size=50)
                bulk_update_payload = []

        # Final update for any remaining objects in the last batch
        if bulk_update_payload:
            logger.info(f"Updating Cost Codes | WORKSPACE_ID: {workspace_id} | COUNT: {len(bulk_update_payload)}")
            CostCode.objects.bulk_update(bulk_update_payload, ['project_id', 'project_name', 'updated_at'], batch_size=50)


def reset_flag_and_disable_cost_type_field(workspace_id: int, reset_flag: bool) -> None:
    """
    Reset the flag and disable the cost type field
    :param workspace_id: Workspace ID
    :param reset_flag: Flag to enable/disable the cost type field in Fyle
    :return: None
    """
    if not reset_flag:
        return

    platform = connect_to_platform(workspace_id)

    instance = DependentFieldSetting.objects.filter(workspace_id=workspace_id).first()

    cost_type_field_id = None
    cost_type_field_id = instance.cost_type_field_id

    if cost_type_field_id:
        logger.info("Resetting Cost Type Import Flag to %s | WORKSPACE_ID: %s", instance.is_cost_type_import_enabled, workspace_id)
        create_dependent_custom_field_in_fyle(
            workspace_id=instance.workspace_id,
            fyle_attribute_type=instance.cost_type_field_name,
            platform=platform,
            source_placeholder=instance.cost_type_placeholder,
            parent_field_id=instance.cost_code_field_id,
            cost_type_id=cost_type_field_id,
            is_enabled=instance.is_cost_type_import_enabled
        )

    # Update the is_imported flag to False for all the cost types so
    # that when the import is enabled again, all the cost types are imported
    BATCH_SIZE = 500
    cost_types_queryset = CostType.objects.filter(
        workspace_id=instance.workspace_id,
        is_imported=True
    )

    bulk_update_payload = []

    for cost_type in cost_types_queryset.iterator(chunk_size=BATCH_SIZE):
        cost_type.is_imported = False
        bulk_update_payload.append(cost_type)

        if len(bulk_update_payload) >= BATCH_SIZE:
            logger.info(f"Updating Cost Types Import Flag | WORKSPACE_ID: {instance.workspace_id} | COUNT: {len(bulk_update_payload)}")
            CostType.objects.bulk_update(bulk_update_payload, ['is_imported'], batch_size=50)
            bulk_update_payload = []

    # Final update for any remaining objects in the last batch
    if bulk_update_payload:
        logger.info(f"Updating Cost Types Import Flag | WORKSPACE_ID: {instance.workspace_id} | COUNT: {len(bulk_update_payload)}")
        CostType.objects.bulk_update(bulk_update_payload, ['is_imported'], batch_size=50)
