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