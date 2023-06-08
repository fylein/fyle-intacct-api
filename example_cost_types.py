# This script is for org `oryVGi2hkIje` Fyle for Multiorg Dashboard 3 on Staging

import json
from django.contrib.postgres.aggregates import ArrayAgg
from fyle_integrations_platform_connector import PlatformConnector
from apps.sage_intacct.models import CostTypes
from apps.workspaces.models import FyleCredential

# Fyle for multi org dashboard 1
project_field_id = 184987
task_field_id = 220103
cost_type_field_id = 220104

# Fyle for multi dashboard 3
project_field_id = 186164
task_field_id = 221214
cost_type_field_id = 221215

file = open("response.json", "r")
response = json.load(file)
workspace_id = 2
creds = FyleCredential.objects.get(workspace_id=workspace_id)
connector = PlatformConnector(creds)

CostTypes.bulk_create_or_update(response, workspace_id)

projects = CostTypes.objects.filter(workspace_id=workspace_id).values('project_name').annotate(tasks=ArrayAgg('task_name', distinct=True))
tasks = CostTypes.objects.filter(workspace_id=workspace_id).values('task_name').annotate(cost_types=ArrayAgg('name', distinct=True))

print('No. of Task Batches - ', projects.count())
print('No. of Cost Type Batches - ', tasks.count())

projects_payload = []

for project in projects:
    projects_payload.append({
        'name': project['project_name'],
        'code': project['project_name'],
        'description': 'Sage Intacct Project',
        'is_enabled': True
    })

connector.projects.post_bulk(projects_payload)

for project in projects:
    payload = [
        {
            "parent_expense_field_id": project_field_id,
            'parent_expense_field_value': project['project_name'],
            'expense_field_id': task_field_id,
            'expense_field_value': task,
            'is_enabled': True
        } for task in project['tasks']
    ]
    connector.expense_fields.bulk_post_dependent_expense_field_values(payload)

for task in tasks:
    payload = [
        {
            "parent_expense_field_id": task_field_id,
            'parent_expense_field_value': task['task_name'],
            'expense_field_id': cost_type_field_id,
            'expense_field_value': cost_type,
            'is_enabled': True
        } for cost_type in task['cost_types']
    ]
    connector.expense_fields.bulk_post_dependent_expense_field_values(payload)




# ASHWIN'S ROUGH CODE
from fyle_accounting_mappings.models import MappingSetting, ExpenseField
from apps.workspaces.models import FyleCredential
from fyle_integrations_platform_connector import PlatformConnector
from apps.mappings.tasks import create_dependent_custom_field_in_fyle, post_dependent_expense_field_values
from django.contrib.postgres.aggregates import ArrayAgg
from apps.sage_intacct.models import CostType

workspace_id = 2

MappingSetting.objects.create(
    workspace_id=2,
    source_field='PROJECT',
    destination_field='PROJECT',
    import_to_fyle=True,
    is_custom=False,
    expense_field=ExpenseField.objects.get(attribute_type='PROJECT')
)

MappingSetting.objects.create(
    workspace_id=2,
    source_field='INTACCT_TASK',
    destination_field='TASK',
    import_to_fyle=True,
    is_custom=True,
    expense_field=None
)

fyle_credentials: FyleCredential = FyleCredential.objects.get(workspace_id=workspace_id)
platform = PlatformConnector(fyle_credentials=fyle_credentials)

create_dependent_custom_field_in_fyle(
    workspace_id=workspace_id,
    fyle_attribute_type='INTACCT_TASK',
    platform=platform,
    parent_field_id=182585,
    source_placeholder='Dummy placeholder 1'
)

MappingSetting.objects.create(
    workspace_id=2,
    source_field='INTACCT_COST_TYPE',
    destination_field='COST_TYPE',
    import_to_fyle=True,
    is_custom=False,
    expense_field=None
)

create_dependent_custom_field_in_fyle(
    workspace_id=workspace_id,
    fyle_attribute_type='INTACCT_COST_TYPE',
    platform=platform,
    parent_field_id=225515,
    source_placeholder='Dummy placeholder 2'
)


# post_dependent_expense_field_values(
#     workspace_id=workspace_id,
#     platform=platform
# )
projects = CostType.objects.filter(workspace_id=workspace_id).values('project_name').annotate(tasks=ArrayAgg('task_name', distinct=True))
tasks = CostType.objects.filter(workspace_id=workspace_id).values('task_name').annotate(cost_types=ArrayAgg('name', distinct=True))

project_field_id = ExpenseField.objects.get(attribute_type='PROJECT', workspace_id=workspace_id).source_field_id

task_mapping = MappingSetting.objects.get(workspace_id=workspace_id, destination_field='TASK')
task_field_id = ExpenseField.objects.get(attribute_type=task_mapping.source_field, workspace_id=workspace_id).source_field_id

cost_type_mapping = MappingSetting.objects.get(workspace_id=workspace_id, destination_field='COST_TYPE')
cost_type_field_id = ExpenseField.objects.get(attribute_type=cost_type_mapping.source_field, workspace_id=workspace_id).source_field_id


for project in projects:
    payload = [
        {
            'parent_expense_field_id': project_field_id,
            'parent_expense_field_value': project['project_name'],
            'expense_field_id': task_field_id,
            'expense_field_value': task,
            'is_enabled': True
        } for task in project['tasks']
    ]
    print('111 payload', payload)
    platform.expense_fields.bulk_post_dependent_expense_field_values(payload)

for task in tasks:
    payload = [
        {
            'parent_expense_field_id': task_field_id,
            'parent_expense_field_value': task['task_name'],
            'expense_field_id': cost_type_field_id,
            'expense_field_value': cost_type,
            'is_enabled': True
        } for cost_type in task['cost_types']
    ]
    print('222 payload', payload)
    platform.expense_fields.bulk_post_dependent_expense_field_values(payload)
