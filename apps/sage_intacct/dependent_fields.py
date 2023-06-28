import logging
from datetime import datetime
from typing import Dict
from time import sleep

from django_q.models import Schedule

from django.contrib.postgres.aggregates import ArrayAgg
from fyle_integrations_platform_connector import PlatformConnector

from fyle_accounting_mappings.models import ExpenseAttribute

from sageintacctsdk.exceptions import InvalidTokenError, NoPrivilegeError

from apps.fyle.helpers import connect_to_platform
from apps.fyle.models import DependentFieldSetting
from apps.mappings.tasks import construct_custom_field_placeholder, sync_sage_intacct_attributes
from apps.sage_intacct.models import CostType
from apps.workspaces.models import SageIntacctCredential


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def post_dependent_cost_code(dependent_field_setting: DependentFieldSetting, platform: PlatformConnector, filters: Dict):
    projects = CostType.objects.filter(**filters).values('project_name').annotate(tasks=ArrayAgg('task_name', distinct=True))
    projects_from_cost_types = [project['project_name'] for project in projects]

    existing_projects_in_fyle = ExpenseAttribute.objects.filter(
        workspace_id=dependent_field_setting.workspace_id,
        attribute_type='PROJECT',
        value__in=projects_from_cost_types
    ).values_list('value', flat=True)

    for project in projects:
        payload = [
            {
                'parent_expense_field_id': dependent_field_setting.project_field_id,
                'parent_expense_field_value': project['project_name'],
                'expense_field_id': dependent_field_setting.cost_code_field_id,
                'expense_field_value': task,
                'is_enabled': True
            } for task in project['tasks'] if project['project_name'] in existing_projects_in_fyle
        ]
        if payload:
            sleep(0.2)
            platform.expense_fields.bulk_post_dependent_expense_field_values(payload)


def post_dependent_cost_type(dependent_field_setting: DependentFieldSetting, platform: PlatformConnector, filters: Dict):
    tasks = CostType.objects.filter(**filters).values('task_name').annotate(cost_types=ArrayAgg('name', distinct=True))
    tasks_from_cost_types = [task['task_name'] for task in tasks]

    existing_tasks_in_fyle = ExpenseAttribute.objects.filter(
        workspace_id=dependent_field_setting.workspace_id,
        attribute_type=dependent_field_setting.cost_code_field_name.upper().replace(' ', '_'),
        value__in=tasks_from_cost_types
    ).values_list('value', flat=True)

    for task in tasks:
        payload = [
            {
                'parent_expense_field_id': dependent_field_setting.cost_code_field_id,
                'parent_expense_field_value': task['task_name'],
                'expense_field_id': dependent_field_setting.cost_type_field_id,
                'expense_field_value': cost_type,
                'is_enabled': True
            } for cost_type in task['cost_types'] if task['task_name'] in existing_tasks_in_fyle
        ]

        if payload:
            sleep(0.2)
            platform.expense_fields.bulk_post_dependent_expense_field_values(payload)


def post_dependent_expense_field_values(workspace_id: int, dependent_field_setting: DependentFieldSetting, platform: PlatformConnector = None):
    if not platform:
        platform = connect_to_platform(workspace_id)

    filters = {
        'workspace_id': workspace_id
    }

    if dependent_field_setting.last_successful_import_at:
        filters['updated_at__gte'] = dependent_field_setting.last_successful_import_at

    post_dependent_cost_code(dependent_field_setting, platform, filters)
    post_dependent_cost_type(dependent_field_setting, platform, filters)

    DependentFieldSetting.objects.filter(workspace_id=workspace_id).update(last_successful_import_at=datetime.now())


def import_dependent_fields_to_fyle(workspace_id: str):
    dependent_field = DependentFieldSetting.objects.get(workspace_id=workspace_id)

    try:
        platform = connect_to_platform(workspace_id)
        sync_sage_intacct_attributes('COST_TYPE', workspace_id)
        post_dependent_expense_field_values(workspace_id, dependent_field, platform)

    except (SageIntacctCredential.DoesNotExist, InvalidTokenError):
        logger.info('Invalid Token or Sage Intacct credentials does not exist - %s', workspace_id)
    except NoPrivilegeError:
        logger.info('Insufficient permission to access the requested module')
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
