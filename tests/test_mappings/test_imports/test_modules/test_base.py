import pytest
from fyle_accounting_mappings.models import (
    DestinationAttribute, 
    ExpenseAttribute
)
from fyle_integrations_platform_connector import PlatformConnector
from apps.workspaces.models import FyleCredential
from apps.mappings.imports.modules.projects import Project
from .fixtures import data
from .helpers import *

def test_sync_destination_attributes(mocker, db):
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Projects.get_all',
        return_value=data['get_projects_destination_attributes']
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

    # We return an empty list here because we do increamental sync based on the updated_at timestamp.
    # Since we already have values for PROJECT in DB for workspace_id=1, we return an empty list.
    # TODO: Add support for a diffrent workspace where we return a list of projects.
    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Projects.list_all',
        return_value=[]
    )

    projects_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert projects_count == 1244

    project = Project(workspace_id, 'PROJECT')
    project.sync_expense_attributes(platform)

    projects_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert projects_count == 1244

def test__remove_duplicates(db):
    attributes = DestinationAttribute.objects.filter(attribute_type='EMPLOYEE')
    
    assert len(attributes) == 55

    for attribute in attributes:
        DestinationAttribute.objects.create(
            attribute_type='EMPLOYEE',
            workspace_id=attribute.workspace_id,
            value=attribute.value,
            destination_id='010{0}'.format(attribute.destination_id)
        )

    attributes = DestinationAttribute.objects.filter(attribute_type='EMPLOYEE')

    assert len(attributes) == 110

    base = get_base_class_instance()

    attributes = base._Base__remove_duplicate_attributes(attributes)
    assert len(attributes) == 55


def test__get_platform_class(db):
    base = get_base_class_instance()
    platform = get_platform_connection(1)

    assert base._Base__get_platform_class(platform) == platform.projects

    base = get_base_class_instance(workspace_id=1, source_field='CATEGORY', destination_field='ACCOUNT', class_name='categories')
    assert base._Base__get_platform_class(platform) == platform.categories

    base = get_base_class_instance(workspace_id=1, source_field='COST_CENTER', destination_field='DEPARTMENT', class_name='cost_centers')
    assert base._Base__get_platform_class(platform) == platform.cost_centers

def test__get_auto_sync_permission(db):
    base = get_base_class_instance()

    assert base._Base__get_auto_sync_permission() == True

    base = get_base_class_instance(workspace_id=1, source_field='CATEGORY', destination_field='ACCOUNT', class_name='categories')

    assert base._Base__get_auto_sync_permission() == True

    base = get_base_class_instance(workspace_id=1, source_field='COST_CENTER', destination_field='DEPARTMENT', class_name='cost_centers')

    assert base._Base__get_auto_sync_permission() == False

# def test_check_import_log_and_start_import(db):
#     base = get_base_class_instance()

#     # Not create case
#     ImportLog.objects.create(
#         workspace_id=3,
#         attribute_type='PROJECT',
#         status='IN_PROGRESS'
#     )
#     assert base.check_import_log_and_start_import() == None
    
#     ImportLog.objects.all().delete()

#     # create case
#     base.check_import_log_and_start_import()
#     import_log = ImportLog.objects.get(workspace_id=1, attribute_type='PROJECT')
#     assert import_log.status == 'IN_PROGRESS'
#     assert import_log.processed_batches_count == 0
#     assert import_log.total_batches_count == 0
