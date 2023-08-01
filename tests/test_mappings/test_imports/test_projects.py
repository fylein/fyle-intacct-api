# import pytest
# from apps.mappings.imports.projects import Project
# from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute
# from fyle_integrations_platform_connector import PlatformConnector
# from apps.workspaces.models import FyleCredential
# from .fixtures import data

# def test_sync_destination_attributes(mocker, db):
#     workspace_id = 1

#     mocker.patch(
#         'sageintacctsdk.apis.Projects.get_all',
#         return_value=data['get_projects']
#     )
#     mocker.patch(
#         'sageintacctsdk.apis.Projects.count',
#         return_value=18
#     )

#     project_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
#     assert project_count == 16

#     project = Project(workspace_id, 'PROJECT')
#     project.sync_destination_attributes('PROJECT')

#     new_project_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
#     assert new_project_count == 18

# def test_sync_expense_atrributes(mocker, db):
#     workspace_id = 1
#     fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
#     platform = PlatformConnector(fyle_credentials=fyle_credentials)

#     mocker.patch(
#         'fyle.platform.apis.v1beta.admin.Projects.list_all',
#         return_value=[]
#     )

#     project = Project(workspace_id, 'PROJECT')
#     project.sync_expense_attributes(platform)

#     projects_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
#     assert projects_count == 1244
