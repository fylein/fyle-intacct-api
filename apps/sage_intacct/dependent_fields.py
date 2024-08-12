import logging
from datetime import datetime, timezone
from typing import Dict, List
from time import sleep

from django.contrib.postgres.fields import JSONField
from django.db.models import F, Func, Value

from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
from fyle_integrations_platform_connector import PlatformConnector

from fyle_accounting_mappings.models import ExpenseAttribute

from sageintacctsdk.exceptions import (
    InvalidTokenError,
    NoPrivilegeError,
    SageIntacctSDKError
)
from fyle.platform.exceptions import InvalidTokenError as FyleInvalidTokenError

from apps.fyle.helpers import connect_to_platform
from apps.fyle.models import DependentFieldSetting
from apps.mappings.tasks import sync_sage_intacct_attributes
from apps.sage_intacct.models import CostType
from apps.workspaces.models import SageIntacctCredential
from apps.mappings.models import ImportLog
from apps.mappings.exceptions import handle_import_exceptions
from apps.workspaces.models import Configuration
from apps.mappings.helpers import prepend_code_to_name

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def construct_custom_field_placeholder(source_placeholder: str, fyle_attribute: str, existing_attribute: Dict):
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
def post_dependent_cost_code(import_log: ImportLog, dependent_field_setting: DependentFieldSetting, platform: PlatformConnector, filters: Dict, is_enabled: bool = True):
    configuration = Configuration.objects.filter(workspace_id=dependent_field_setting.workspace_id).first()

    last_successful_run_at = datetime.now(timezone.utc)
    use_job_code_in_naming = 'PROJECT' in configuration.import_code_fields
    use_cost_code_in_naming = 'COST_CODE' in configuration.import_code_fields

    BATCH_SIZE = 200
    posted_cost_codes = []
    processed_batches = 0
    is_errored = False
    cost_type_ids = []

    cost_types = CostType.objects.filter(**filters).values_list('id', flat=True)

    for cost_type_id in cost_types.iterator(chunk_size=BATCH_SIZE):
        cost_type_ids.append(cost_type_id)

        if len(cost_type_ids) >= BATCH_SIZE:
            batches_processed, batch_errored = process_cost_code_batch(
                platform,
                cost_type_ids,
                posted_cost_codes,
                use_job_code_in_naming,
                use_cost_code_in_naming,
                dependent_field_setting,
                is_enabled
            )
            processed_batches += batches_processed
            is_errored = is_errored and batch_errored
            cost_type_ids = []

    if cost_type_ids:
        batches_processed, batch_errored = process_cost_code_batch(
            platform,
            cost_type_ids,
            posted_cost_codes,
            use_job_code_in_naming,
            use_cost_code_in_naming,
            dependent_field_setting,
            is_enabled
        )
        processed_batches += batches_processed
        is_errored = is_errored and batch_errored

    import_log.status = 'PARTIALLY_FAILED' if is_errored else 'COMPLETE'
    import_log.error_log = []
    import_log.processed_batches_count = processed_batches
    if not is_errored:
        import_log.last_successful_run_at = last_successful_run_at
    import_log.save()

    return posted_cost_codes, is_errored


def process_cost_code_batch(
    platform: PlatformConnector,
    cost_type_ids: List[int],
    posted_cost_codes: List[str],
    use_job_code_in_naming: bool,
    use_cost_code_in_naming: bool,
    dependent_field_setting: DependentFieldSetting,
    is_enabled: bool
):
    processed_batches = 0
    is_errored = False

    projects_batch = (
        CostType.objects.filter(workspace_id=dependent_field_setting.workspace_id, id__in=cost_type_ids)
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

    for project in projects_batch:
        payload = []
        cost_code_names = []
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
                cost_code_names.append(cost_code['cost_code_name'])

            if payload:
                sleep(0.2)
                try:
                    platform.dependent_fields.bulk_post_dependent_expense_field_values(payload)
                    posted_cost_codes.extend(cost_code_names)
                    processed_batches += 1
                except Exception as exception:
                    is_errored = True
                    logger.error(f'Exception while posting dependent cost code | Error: {exception} | Payload: {payload}')

    return processed_batches, is_errored


@handle_import_exceptions
def post_dependent_cost_type(import_log: ImportLog, dependent_field_setting: DependentFieldSetting, platform: PlatformConnector, filters: Dict):
    configuration = Configuration.objects.filter(workspace_id=dependent_field_setting.workspace_id).first()

    last_successful_run_at = datetime.now(timezone.utc)
    use_cost_code_in_naming = 'COST_CODE' in configuration.import_code_fields
    use_cost_type_code_in_naming = 'COST_TYPE' in configuration.import_code_fields

    BATCH_SIZE = 200
    processed_batches = 0
    is_errored = False
    cost_type_ids = []

    cost_types = CostType.objects.filter(is_imported=False, **filters).values_list('id', flat=True)

    for cost_type_id in cost_types.iterator(chunk_size=BATCH_SIZE):
        cost_type_ids.append(cost_type_id)

        if len(cost_type_ids) >= BATCH_SIZE:
            batches_processed, batch_errored = process_cost_type_batch(
                platform,
                filters,
                cost_type_ids,
                use_cost_code_in_naming,
                use_cost_type_code_in_naming,
                dependent_field_setting
            )
            processed_batches += batches_processed
            is_errored = is_errored and batch_errored
            cost_type_ids = []

    if cost_type_ids:
        batches_processed, batch_errored = process_cost_type_batch(
            platform,
            filters,
            cost_type_ids,
            use_cost_code_in_naming,
            use_cost_type_code_in_naming,
            dependent_field_setting
        )
        processed_batches += batches_processed
        is_errored = is_errored and batch_errored

    import_log.status = 'PARTIALLY_FAILED' if is_errored else 'COMPLETE'
    import_log.error_log = []
    import_log.processed_batches_count = processed_batches
    if not is_errored:
        import_log.last_successful_run_at = last_successful_run_at
    import_log.save()

    return is_errored


def process_cost_type_batch(
    platform: PlatformConnector,
    filters: Dict,
    cost_type_ids: List[int],
    use_cost_code_in_naming: bool,
    use_cost_type_code_in_naming: bool,
    dependent_field_setting: DependentFieldSetting
):
    processed_batches = 0
    is_errored = False

    cost_types_batch = (
        CostType.objects.filter(id__in=cost_type_ids)
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
                platform.dependent_fields.bulk_post_dependent_expense_field_values(payload)
                CostType.objects.filter(task_name=cost_types['task_name'], task_id=cost_types['task_id'], workspace_id=dependent_field_setting.workspace_id).update(is_imported=True)
                processed_batches += 1
            except Exception as exception:
                is_errored = True
                logger.error(f'Exception while posting dependent cost type | Error: {exception} | Payload: {payload}')

    return processed_batches, is_errored


def post_dependent_expense_field_values(workspace_id: int, dependent_field_setting: DependentFieldSetting, platform: PlatformConnector = None, cost_code_import_log: ImportLog = None, cost_type_import_log: ImportLog = None):
    if not platform:
        platform = connect_to_platform(workspace_id)

    filters = {
        'workspace_id': workspace_id
    }

    if dependent_field_setting.last_successful_import_at:
        filters['updated_at__gte'] = dependent_field_setting.last_successful_import_at

    posted_cost_types, is_cost_code_errored = post_dependent_cost_code(cost_code_import_log, dependent_field_setting, platform, filters)
    if posted_cost_types:
        filters['task_name__in'] = posted_cost_types

    if cost_code_import_log.status in ['FAILED', 'FATAL']:
        cost_type_import_log.status = 'FAILED'
        cost_type_import_log.error_log = {'message': 'Importing COST_CODE failed'}
        cost_type_import_log.save()
        return
    else:
        is_cost_type_errored = post_dependent_cost_type(cost_type_import_log, dependent_field_setting, platform, filters)
        if not is_cost_type_errored and not is_cost_code_errored and cost_type_import_log.processed_batches_count > 0:
            DependentFieldSetting.objects.filter(workspace_id=workspace_id).update(last_successful_import_at=datetime.now())


def import_dependent_fields_to_fyle(workspace_id: str):
    dependent_field = DependentFieldSetting.objects.get(workspace_id=workspace_id)

    try:
        platform = connect_to_platform(workspace_id)
        cost_code_import_log = ImportLog.update_or_create(attribute_type='COST_CODE', workspace_id=workspace_id)
        cost_type_import_log = ImportLog.update_or_create(attribute_type='COST_TYPE', workspace_id=workspace_id)
        sync_sage_intacct_attributes('COST_TYPE', workspace_id, cost_type_import_log)
        if cost_code_import_log.status == 'IN_PROGRESS' and cost_type_import_log.status == 'IN_PROGRESS':
            post_dependent_expense_field_values(workspace_id, dependent_field, platform, cost_code_import_log, cost_type_import_log)
        else:
            logger.error('Importing dependent fields to fyle failed | CONTENT: {{WORKSPACE_ID: {}}}'.format(workspace_id))
    except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
        logger.info('Invalid Token or Sage Intacct credentials does not exist - %s', workspace_id)
    except NoPrivilegeError:
        logger.info('Insufficient permission to access the requested module')
    except FyleInvalidTokenError:
        logger.info('Invalid Token or Fyle credentials does not exist - %s', workspace_id)
    except SageIntacctSDKError as exception:
        logger.info('Sage Intacct SDK Error - %s', exception)
    except Exception as exception:
        logger.error('Exception while importing dependent fields to fyle - %s', exception)


def create_dependent_custom_field_in_fyle(workspace_id: int, fyle_attribute_type: str, platform: PlatformConnector, parent_field_id: str, source_placeholder: str = None):
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
        'is_enabled': True,
        'is_mandatory': False,
        'placeholder': placeholder,
        'options': [],
        'parent_field_id': parent_field_id,
        'code': None
    }

    return platform.expense_custom_fields.post(expense_custom_field_payload)


def update_and_disable_cost_code(workspace_id: int, cost_codes_to_disable: Dict, platform: PlatformConnector):
    """
    Update the job_name in CostType and disable the old cost code in Fyle
    """
    dependent_field_setting = DependentFieldSetting.objects.filter(is_import_enabled=True, workspace_id=workspace_id).first()

    if dependent_field_setting:
        filters = {
            'project_id__in': list(cost_codes_to_disable.keys()),
            'workspace_id': workspace_id
        }
        cost_code_import_log = ImportLog.update_or_create('COST_CODE', workspace_id)
        # This call will disable the cost codes in Fyle that has old project name
        posted_cost_codes = post_dependent_cost_code(cost_code_import_log, dependent_field_setting, platform, filters, is_enabled=False)

        logger.info(f"Disabled Cost Codes in Fyle | WORKSPACE_ID: {workspace_id} | COUNT: {len(posted_cost_codes)}")
