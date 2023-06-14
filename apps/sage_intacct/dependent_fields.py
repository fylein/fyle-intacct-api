import logging
from datetime import datetime

from django_q.models import Schedule
from django.contrib.postgres.aggregates import ArrayAgg
from fyle_integrations_platform_connector import PlatformConnector

from fyle_accounting_mappings.models import ExpenseAttribute


from sageintacctsdk.exceptions import InvalidTokenError, NoPrivilegeError

from apps.fyle.helpers import connect_to_platform
from apps.fyle.models import DependentField
from apps.mappings.tasks import construct_custom_field_placeholder
from apps.sage_intacct.models import CostType
from apps.workspaces.models import SageIntacctCredential


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def post_dependent_expense_field_values(workspace_id: int, dependent_field: DependentField, platform: PlatformConnector = None):
    if not platform:
        platform = connect_to_platform(workspace_id)

    # JSONBAgg get both status
    # projects = CostType.objects.filter(workspace_id=workspace_id).values('project_name').annotate(tasks=JSONBAgg('task_name', distinct=True))
    # tasks = CostType.objects.filter(workspace_id=workspace_id).values('task_name').annotate(cost_types=JSONBAgg('name', distinct=True))
    projects = CostType.objects.filter(workspace_id=workspace_id).values('project_name').annotate(tasks=ArrayAgg('task_name', distinct=True))
    tasks = CostType.objects.filter(workspace_id=workspace_id).values('task_name').annotate(cost_types=ArrayAgg('name', distinct=True))

    # TODO: check auto-sync possibility, via sdk

    # check if we can cancel the 2nd task in same chain
    # chain.append('task post')
    # chain.append('cost type post')

    # TODO: remove sync of dependent fields for fyle refresh

    for project in projects:
        payload = [
            {
                'parent_expense_field_id': dependent_field.project_field_id,
                'parent_expense_field_value': project['project_name'],
                'expense_field_id': dependent_field.cost_code_field_id,
                'expense_field_value': task,
                'is_enabled': True
            } for task in project['tasks']
        ]
        platform.expense_fields.bulk_post_dependent_expense_field_values(payload)

    for task in tasks:
        payload = [
            {
                'parent_expense_field_id': dependent_field.cost_code_field_id,
                'parent_expense_field_value': task['task_name'],
                'expense_field_id': dependent_field.cost_type_field_id,
                'expense_field_value': cost_type,
                'is_enabled': True
            } for cost_type in task['cost_types']
        ]
        platform.expense_fields.bulk_post_dependent_expense_field_values(payload)


def import_dependent_fields_to_fyle(workspace_id: str):
    dependent_field = DependentField.objects.get(workspace_id=workspace_id)
    platform = connect_to_platform(workspace_id)
    # TODO: call sync_cost_types which should sync tasks and cost types
    # sync_sage_intacct_attributes(mapping_setting.destination_field, workspace_id)

    try:
        post_dependent_expense_field_values(workspace_id, dependent_field, platform)

    except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
        logger.info('Invalid Token or Sage Intacct credentials does not exist - %s', workspace_id)
    except NoPrivilegeError:
        logger.info('Insufficient permission to access the requested module')


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

    created_field = platform.expense_custom_fields.post(expense_custom_field_payload)
    platform.expense_custom_fields.sync()

    return created_field


def schedule_dependent_field_imports(workspace_id: int, is_import_enabled: bool):
    if is_import_enabled:
        Schedule.objects.update_or_create(
            func='apps.sage_intacct.dependent_fields.import_dependent_fields_to_fyle',
            args='{}'.format(workspace_id),
            defaults={
                'schedule_type': Schedule.MINUTES,
                'minutes': 24 * 60,
                'next_run': datetime.now()
            }
        )
    else:
        schedule: Schedule = Schedule.objects.filter(
            func='apps.sage_intacct.dependent_fields.import_dependent_fields_to_fyle',
            args='{}'.format(workspace_id)
        ).first()

        if schedule:
            schedule.delete()
