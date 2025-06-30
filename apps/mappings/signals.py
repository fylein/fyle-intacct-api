import logging
from datetime import datetime, timedelta, timezone

from django.db.models import Q
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, post_delete

from rest_framework.exceptions import ValidationError
from sageintacctsdk.exceptions import InvalidTokenError
from fyle_intacct_api.utils import invalidate_sage_intacct_credentials
from fyle.platform.exceptions import WrongParamsError
from fyle_integrations_platform_connector import PlatformConnector
from fyle_accounting_mappings.models import (
    MappingSetting,
    Mapping,
    EmployeeMapping,
    CategoryMapping,
    DestinationAttribute
)


from apps.tasks.models import Error
from apps.mappings.constants import SYNC_METHODS
from apps.fyle.helpers import update_dimension_details
from apps.workspaces.models import Configuration, FyleCredential, SageIntacctCredential
from fyle_integrations_imports.models import ImportLog
from apps.mappings.models import LocationEntityMapping
from apps.sage_intacct.utils import SageIntacctConnector
from fyle_integrations_imports.modules.expense_custom_fields import ExpenseCustomField
from apps.mappings.schedules import schedule_or_delete_fyle_import_tasks as new_schedule_or_delete_fyle_import_tasks

logger = logging.getLogger(__name__)
logger.level = logging.INFO


@receiver(pre_save, sender=CategoryMapping)
def pre_save_category_mappings(sender: type[CategoryMapping], instance: CategoryMapping, **kwargs) -> None:
    """
    Create CCC mapping if reimbursable type in ER and ccc in (bill, je, ccc)
    """
    if instance.destination_expense_head:
        if instance.destination_expense_head.detail and 'gl_account_no' in instance.destination_expense_head.detail and \
            instance.destination_expense_head.detail['gl_account_no']:

            destination_attribute = DestinationAttribute.objects.filter(
                workspace_id=instance.workspace_id,
                attribute_type='ACCOUNT',
                destination_id=instance.destination_expense_head.detail['gl_account_no']
            ).first()

            instance.destination_account_id = destination_attribute.id


@receiver(post_save, sender=CategoryMapping)
def resolve_post_category_mapping_errors(sender: type[CategoryMapping], instance: Mapping, **kwargs) -> None:
    """
    Resolve errors after mapping is created
    """
    Error.objects.filter(expense_attribute_id=instance.source_category_id).update(is_resolved=True, updated_at=datetime.now(timezone.utc))


@receiver(post_save, sender=EmployeeMapping)
def resolve_post_employees_mapping_errors(sender: type[EmployeeMapping], instance: Mapping, **kwargs) -> None:
    """
    Resolve errors after mapping is created
    """
    Error.objects.filter(expense_attribute_id=instance.source_employee_id).update(is_resolved=True, updated_at=datetime.now(timezone.utc))


@receiver(post_save, sender=LocationEntityMapping)
def run_post_location_entity_mappings(sender: type[LocationEntityMapping], instance: LocationEntityMapping, **kwargs) -> None:
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    workspace = instance.workspace
    workspace.onboarding_state = 'EXPORT_SETTINGS'
    workspace.save()


@receiver(post_delete, sender=LocationEntityMapping)
def run_post_delete_location_entity_mappings(sender: type[LocationEntityMapping], instance: LocationEntityMapping, **kwargs) -> None:
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    workspace = instance.workspace
    if workspace.onboarding_state in ('CONNECTION', 'EXPORT_SETTINGS'):
        DestinationAttribute.objects.filter(~Q(attribute_type='LOCATION_ENTITY'), workspace_id=instance.workspace_id).delete()
        workspace.onboarding_state = 'CONNECTION'
        workspace.save()


@receiver(post_save, sender=MappingSetting)
def run_post_mapping_settings_triggers(sender: type[MappingSetting], instance: MappingSetting, **kwargs) -> None:
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    configuration = Configuration.objects.filter(workspace_id=instance.workspace_id).first()

    if instance.source_field in ['PROJECT', 'COST_CENTER'] or instance.is_custom:
        new_schedule_or_delete_fyle_import_tasks(configuration, instance)


@receiver(pre_save, sender=MappingSetting)
def run_pre_mapping_settings_triggers(sender: type[MappingSetting], instance: MappingSetting, **kwargs) -> None:
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    default_attributes = ['EMPLOYEE', 'CATEGORY', 'PROJECT', 'COST_CENTER', 'TAX_GROUP', 'CORPORATE_CARD']

    instance.source_field = instance.source_field.upper().replace(' ', '_')

    if instance.source_field not in default_attributes and instance.import_to_fyle:
        # TODO: sync intacct fields before we upload custom field
        try:
            workspace_id = int(instance.workspace_id)
            configuration = Configuration.objects.filter(workspace_id=workspace_id).first()
            prepend_code_to_name = False

            if configuration and instance.destination_field in configuration.import_code_fields:
                prepend_code_to_name = True

            # Checking is import_log exists or not if not create one
            import_log, is_created = ImportLog.objects.get_or_create(
                workspace_id=workspace_id,
                attribute_type=instance.source_field,
                defaults={
                    'status': 'IN_PROGRESS'
                }
            )

            last_successful_run_at = None
            if import_log and not is_created:
                last_successful_run_at = import_log.last_successful_run_at if import_log.last_successful_run_at else None
                time_difference = datetime.now() - timedelta(minutes=32)
                offset_aware_time_difference = time_difference.replace(tzinfo=timezone.utc)

                # if the import_log is present and the last_successful_run_at is less than 30mins then we need to update it
                # so that the schedule can run
                if last_successful_run_at and offset_aware_time_difference and (offset_aware_time_difference < last_successful_run_at):
                    import_log.last_successful_run_at = offset_aware_time_difference
                    last_successful_run_at = offset_aware_time_difference
                    import_log.save()

            # Creating the expense_custom_field object with the correct last_successful_run_at value
            sage_intacct_credentials = SageIntacctCredential.get_active_sage_intacct_credentials(workspace_id=workspace_id)
            sage_intacct_connection = SageIntacctConnector(credentials_object=sage_intacct_credentials, workspace_id=workspace_id)

            expense_custom_field = ExpenseCustomField(
                workspace_id=workspace_id,
                source_field=instance.source_field,
                destination_field=instance.destination_field,
                sync_after=last_successful_run_at,
                prepend_code_to_name=prepend_code_to_name,
                sdk_connection=sage_intacct_connection,
                destination_sync_methods=[SYNC_METHODS.get(instance.destination_field, 'user_defined_dimensions')]
            )

            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
            platform = PlatformConnector(fyle_credentials=fyle_credentials)

            # setting the import_log status to IN_PROGRESS
            import_log.status = 'IN_PROGRESS'
            import_log.save()

            expense_custom_field.sync_expense_attributes(platform)
            expense_custom_field.construct_payload_and_import_to_fyle(platform, import_log)
            expense_custom_field.sync_expense_attributes(platform)
            update_dimension_details(platform=platform, workspace_id=workspace_id)

            # NOTE: We are not setting the import_log status to COMPLETE
            # since the post_save trigger will run the import again in async manner
        except WrongParamsError as error:
            logger.error(
                'Error while creating %s workspace_id - %s in Fyle %s %s',
                instance.source_field, instance.workspace_id, error.message, {'error': error.response}
            )
            if error.response and 'message' in error.response:
                raise ValidationError({
                    'message': error.response['message'],
                    'field_name': instance.source_field
                })

        except SageIntacctCredential.DoesNotExist:
            logger.info(
                'Active Sage Intacct credentials not found for workspace_id - %s',
                workspace_id
            )
            raise ValidationError({
                'message': 'Sage Intacct credentials not found in workspace',
                'field_name': instance.source_field
            })

        except InvalidTokenError:
            invalidate_sage_intacct_credentials(workspace_id)
            logger.info('Invalid Sage Intacct Token Error for workspace_id - %s', workspace_id)

            raise ValidationError({
                'message': 'Invalid Sage Intacct Token Error for workspace_id - %s',
                'field_name': instance.source_field
            })

        # setting the import_log.last_successful_run_at to -30mins for the post_save_trigger
        import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type=instance.source_field).first()
        if import_log.last_successful_run_at:
            last_successful_run_at = import_log.last_successful_run_at - timedelta(minutes=30)
            import_log.last_successful_run_at = last_successful_run_at
            import_log.save()
