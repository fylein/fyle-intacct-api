import pytest
from apps.mappings.imports.projects import Project
from fyle_accounting_mappings.models import DestinationAttribute, ExpenseAttribute
from fyle_integrations_platform_connector import PlatformConnector
from apps.workspaces.models import FyleCredential

def test_sync_destination_attributes(mocker, db):
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Projects.get_all',
        return_value=[
            {
                'RECORDNO':'113',
                'PROJECTID':'10066',
                'NAME':'Labhvam 2',
                'DESCRIPTION':'None',
                'CURRENCY':'AUD',
                'PROJECTCATEGORY':'Contract',
                'PROJECTSTATUS':'In Progress',
                'PARENTKEY':'None',
                'PARENTID':'None',
                'PARENTNAME':'None',
                'STATUS':'active',
                'CUSTOMERKEY':'42',
                'CUSTOMERID':'10066',
                'CUSTOMERNAME':'Med dot',
                'PROJECTTYPE':'AMP-Marketing',
                'DEPARTMENTNAME':'Services',
                'LOCATIONID':'600',
                'LOCATIONNAME':'Australia',
                'BUDGETID':'None',
                'MEGAENTITYID':'600',
                'MEGAENTITYNAME':'Australia'
            },
            {
                'RECORDNO':'112',
                'PROJECTID':'10065',
                'NAME':'Labhvam 3',
                'DESCRIPTION':'None',
                'CURRENCY':'AUD',
                'PROJECTCATEGORY':'Contract',
                'PROJECTSTATUS':'In Progress',
                'PARENTKEY':'None',
                'PARENTID':'None',
                'PARENTNAME':'None',
                'STATUS':'active',
                'CUSTOMERKEY':'43',
                'CUSTOMERID':'10065',
                'CUSTOMERNAME':'Med dot',
                'PROJECTTYPE':'AMP-Marketing',
                'DEPARTMENTNAME':'Services',
                'LOCATIONID':'600',
                'LOCATIONNAME':'Australia',
                'BUDGETID':'None',
                'MEGAENTITYID':'600',
                'MEGAENTITYNAME':'Australia'
            }
        ]
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.count',
        return_value=18
    )

    project_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert project_count == 16

    project = Project(workspace_id, 'PROJECT')
    project.sync_destination_attributes('PROJECT')

    new_project_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert new_project_count == 18

def test_sync_expense_atrributes(mocker, db):
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Projects.list_all',
        return_value=[]
    )

    project = Project(workspace_id, 'PROJECT')
    project.sync_expense_attributes(platform)

    projects_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert projects_count == 1244
