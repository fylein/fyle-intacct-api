"""
Mappings Signal
"""
import logging
import json
import traceback
from django.db.models import Q
from datetime import datetime, timedelta, timezone

from rest_framework.exceptions import ValidationError

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django_q.tasks import async_task

from fyle_accounting_mappings.models import (
    MappingSetting,
    Mapping,
    EmployeeMapping,
    CategoryMapping,
    DestinationAttribute
)
from fyle.platform.exceptions import WrongParamsError

from apps.workspaces.models import Configuration
from apps.mappings.helpers import schedule_or_delete_fyle_import_tasks
from apps.mappings.imports.schedules import schedule_or_delete_fyle_import_tasks as new_schedule_or_delete_fyle_import_tasks
from apps.tasks.models import Error
from apps.mappings.models import LocationEntityMapping
from apps.mappings.imports.modules.expense_custom_fields import ExpenseCustomField
from apps.mappings.models import ImportLog
from fyle_integrations_platform_connector import PlatformConnector
from apps.workspaces.models import FyleCredential

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=CategoryMapping)
def pre_save_category_mappings(sender, instance: CategoryMapping, **kwargs):
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


@receiver(post_save, sender=Mapping)
def resolve_post_mapping_errors(sender, instance: Mapping, **kwargs):
    """
    Resolve errors after mapping is created
    """
    if instance.source_type == 'TAX_GROUP':
        Error.objects.filter(expense_attribute_id=instance.source_id).update(
            is_resolved=True
        )
         

@receiver(post_save, sender=CategoryMapping)
def resolve_post_category_mapping_errors(sender, instance: Mapping, **kwargs):
    """
    Resolve errors after mapping is created
    """
    Error.objects.filter(expense_attribute_id=instance.source_category_id).update(
        is_resolved=True
    )


@receiver(post_save, sender=EmployeeMapping)
def resolve_post_employees_mapping_errors(sender, instance: Mapping, **kwargs):
    """
    Resolve errors after mapping is created
    """
    Error.objects.filter(expense_attribute_id=instance.source_employee_id).update(
        is_resolved=True
    )


@receiver(post_save, sender=LocationEntityMapping)
def run_post_location_entity_mappings(sender, instance: LocationEntityMapping, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    workspace = instance.workspace
    workspace.onboarding_state = 'EXPORT_SETTINGS'
    workspace.save()


@receiver(post_delete, sender=LocationEntityMapping)
def run_post_delete_location_entity_mappings(sender, instance: LocationEntityMapping, **kwargs):
    workspace = instance.workspace
    if workspace.onboarding_state in ('CONNECTION', 'EXPORT_SETTINGS'):
        DestinationAttribute.objects.filter(~Q(attribute_type='LOCATION_ENTITY'), workspace_id=instance.workspace_id).delete()
        workspace.onboarding_state = 'CONNECTION'
        workspace.save()


@receiver(post_save, sender=MappingSetting)
def run_post_mapping_settings_triggers(sender, instance: MappingSetting, **kwargs):
    """
    :param sender: Sender Class
    :param instance: Row instance of Sender Class
    :return: None
    """
    configuration = Configuration.objects.filter(workspace_id=instance.workspace_id).first()
    print("""

        post save mapping setting signal

        """)

    if instance.source_field == 'PROJECT':
        schedule_or_delete_fyle_import_tasks(configuration)
        new_schedule_or_delete_fyle_import_tasks(configuration, instance)

    if instance.source_field == 'COST_CENTER':
        new_schedule_or_delete_fyle_import_tasks(configuration, instance)

    if instance.is_custom:
        print("is custom block has been enetered") 
        new_schedule_or_delete_fyle_import_tasks(configuration, instance)

@receiver(pre_save, sender=MappingSetting)
def run_pre_mapping_settings_triggers(sender, instance: MappingSetting, **kwargs):
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
            print("""

                pre save mapping setting signal

            """)
            print(instance.source_field)
            print(instance.destination_field)
            workspace_id = int(instance.workspace_id)
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
                print("Entered if block for subsequent  runs")
                last_successful_run_at = import_log.last_successful_run_at if import_log.last_successful_run_at else None
                time_difference = datetime.now() - timedelta(minutes=32)
                offset_aware_time_difference = time_difference.replace(tzinfo=timezone.utc)

                # if the import_log is present and the last_successful_run_at is less than 30mins then we need to update it
                # so that the schedule can run
                if last_successful_run_at and offset_aware_time_difference\
                 and (offset_aware_time_difference < last_successful_run_at):
                    import_log.last_successful_run_at = offset_aware_time_difference
                    last_successful_run_at = offset_aware_time_difference
                    import_log.save()

            # Creating the expense_custom_field object with the correct last_successful_run_at value
            expense_custom_field = ExpenseCustomField(
                workspace_id=workspace_id,
                source_field=instance.source_field,
                destination_field=instance.destination_field,
                sync_after=last_successful_run_at
            )

            fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
            platform = PlatformConnector(fyle_credentials=fyle_credentials)

            # setting the import_log status to IN_PROGRESS
            import_log.status = 'IN_PROGRESS'
            import_log.save()

            expense_custom_field.construct_payload_and_import_to_fyle(platform, import_log)
            expense_custom_field.sync_expense_attributes(platform)

            # NOTE: We are not setting the import_log status to COMPLETE 
            # since the post_save trigger will run the import again in async manner

        except WrongParamsError as error:
            print("""


                WrongParamsError block""")
            logger.error(
                'Error while creating %s workspace_id - %s in Fyle %s %s',
                instance.source_field, instance.workspace_id, error.message, {'error': error.response}
            )
            if error.response:
                print("""

                    Error response block

                """)
                print(error.response['message'])
                error_log = {
                    'task': 'Import {0} to Fyle and Auto Create Mappings'.format(instance.source_field),
                    'workspace_id': workspace_id,
                    'message': None,
                    'response': error.response['message']
                }

                import_log = ImportLog.objects.filter(
                    workspace_id=workspace_id,
                    attribute_type=instance.source_field
                ).first()

                print(error_log)

                import_log.error_log = error_log
                import_log.status = 'FAILED'
                import_log.save()
                response = error.response
                if response and 'message' in response and \
                    response['message'] == ('duplicate key value violates unique constraint '
                    '"idx_expense_fields_org_id_field_name_is_enabled_is_custom"'):
                    raise ValidationError({
                        'message': 'Duplicate custom field name',
                        'field_name': instance.source_field
                    })

        # setting the import_log.last_successful_run_at to -30mins for the post_save_trigger
        import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type=instance.source_field).first()
        if import_log.last_successful_run_at:
            last_successful_run_at = import_log.last_successful_run_at - timedelta(minutes=30)
            import_log.last_successful_run_at = last_successful_run_at
            import_log.save()
