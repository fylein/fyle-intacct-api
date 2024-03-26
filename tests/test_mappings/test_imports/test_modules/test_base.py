import pytest
from datetime import (
    datetime,
    timezone,
    timedelta
)
from fyle_accounting_mappings.models import (
    DestinationAttribute, 
    ExpenseAttribute,
    Mapping,
    CategoryMapping
)
from unittest import mock
from fyle_integrations_platform_connector import PlatformConnector
from apps.workspaces.models import FyleCredential, Workspace
from apps.mappings.imports.modules.projects import Project
from apps.mappings.imports.modules.categories import Category
from apps.mappings.models import ImportLog
from .fixtures import data as destination_attributes_data
from apps.tasks.models import Error
from .helpers import *


def test_sync_destination_attributes(mocker, db):
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Projects.get_all',
        return_value=destination_attributes_data['get_projects_destination_attributes']
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.count',
        return_value=18
    )

    project_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert project_count == 16

    project = Project(workspace_id, 'PROJECT', None)
    project.sync_destination_attributes('PROJECT')

    new_project_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert new_project_count == 18


def test_sync_expense_atrributes(mocker, db):
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credentials.workspace.fyle_org_id = 'orqjgyJ21uge'
    fyle_credentials.workspace.save()
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Projects.list_all',
        return_value=[]
    )

    projects_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert projects_count == 1244

    project = Project(workspace_id, 'PROJECT', None)
    project.sync_expense_attributes(platform)

    projects_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert projects_count == 1244

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Projects.list_all',
        return_value=destination_attributes_data['create_new_auto_create_projects_expense_attributes_0']
    )
    project.sync_expense_attributes(platform)

    projects_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert projects_count == 1244 + destination_attributes_data['create_new_auto_create_projects_expense_attributes_0'][0]['count']


def test_remove_duplicates(db):
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

    attributes = base.remove_duplicate_attributes(attributes)
    assert len(attributes) == 55

def test_get_platform_class(db):
    base = get_base_class_instance()
    platform = get_platform_connection(1)

    assert base.get_platform_class(platform) == platform.projects

    base = get_base_class_instance(workspace_id=1, source_field='CATEGORY', destination_field='ACCOUNT', platform_class_name='categories')
    assert base.get_platform_class(platform) == platform.categories

    base = get_base_class_instance(workspace_id=1, source_field='COST_CENTER', destination_field='DEPARTMENT', platform_class_name='cost_centers')
    assert base.get_platform_class(platform) == platform.cost_centers

def test_get_auto_sync_permission(db):
    base = get_base_class_instance()

    assert base.get_auto_sync_permission() == True

    base = get_base_class_instance(workspace_id=1, source_field='CATEGORY', destination_field='ACCOUNT', platform_class_name='categories')

    assert base.get_auto_sync_permission() == True

    base = get_base_class_instance(workspace_id=1, source_field='COST_CENTER', destination_field='DEPARTMENT', platform_class_name='cost_centers')

    assert base.get_auto_sync_permission() == False

def test_construct_attributes_filter(db):
    base = get_base_class_instance()

    assert base.construct_attributes_filter('PROJECT') == {'attribute_type': 'PROJECT', 'workspace_id': 1}

    date_string = '2023-08-06 12:50:05.875029'
    sync_after = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S.%f')


    base = get_base_class_instance(workspace_id=1, source_field='CATEGORY', destination_field='ACCOUNT', platform_class_name='categories', sync_after=sync_after)

    assert base.construct_attributes_filter('CATEGORY') == {'attribute_type': 'CATEGORY', 'workspace_id': 1, 'updated_at__gte': sync_after}

    paginated_destination_attribute_values = ['Mobile App Redesign', 'Platform APIs', 'Fyle NetSuite Integration', 'Fyle Sage Intacct Integration', 'Support Taxes', 'T&M Project with Five Tasks', 'Fixed Fee Project with Five Tasks', 'General Overhead', 'General Overhead-Current', 'Youtube proj', 'Integrations', 'Yujiro', 'Pickle']

    assert base.construct_attributes_filter('COST_CENTER', paginated_destination_attribute_values) == {'attribute_type': 'COST_CENTER', 'workspace_id': 1, 'updated_at__gte': sync_after, 'value__in': paginated_destination_attribute_values}


def test_auto_create_destination_attributes(mocker, db):
    project = Project(1, 'PROJECT', None)
    project.sync_after = None

    Workspace.objects.filter(id=1).update(fyle_org_id='orqjgyJ21uge')
    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(workspace_id=1, source_type='PROJECT', destination_type='PROJECT').delete()
    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT').delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT').delete()

    # create new case for projects import
    with mock.patch('fyle.platform.apis.v1beta.admin.Projects.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.Projects.post_bulk',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.Projects.count',
            return_value=18
        )
        mocker.patch(
            'sageintacctsdk.apis.Projects.get_all',
            return_value=destination_attributes_data['create_new_auto_create_projects_destination_attributes']
        )
        mock_call.side_effect = [
            destination_attributes_data['create_new_auto_create_projects_expense_attributes_0'],
            destination_attributes_data['create_new_auto_create_projects_expense_attributes_1'] 
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'PROJECT').count()

        assert expense_attributes_count == 0

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='PROJECT', destination_type='PROJECT').count()
        
        assert mappings_count == 0

        project.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'PROJECT').count()

        assert expense_attributes_count == destination_attributes_data['create_new_auto_create_projects_expense_attributes_0'][0]['count'] + destination_attributes_data['create_new_auto_create_projects_expense_attributes_1'][0]['count']

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='PROJECT', destination_type='PROJECT').count()
        
        assert mappings_count == 13


    # disable case for project import
    with mock.patch('fyle.platform.apis.v1beta.admin.Projects.list_all') as mock_call:
        mocker.patch(
            'sageintacctsdk.apis.Projects.count',
            return_value=18
        )
        mocker.patch(
            'sageintacctsdk.apis.Projects.get_all',
            return_value=destination_attributes_data['create_new_auto_create_projects_destination_attributes_disable_case']
        )
        mocker.patch(
            'fyle_integrations_platform_connector.apis.Projects.post_bulk',
            return_value=[]
        )

        mock_call.side_effect = [
            destination_attributes_data['create_new_auto_create_projects_expense_attributes_3'],
            destination_attributes_data['create_new_auto_create_projects_expense_attributes_4'] 
        ]

        
        destination_attribute = DestinationAttribute.objects.filter(workspace_id=1, value='Electro wizard').first()
        
        assert destination_attribute.active == True

        expense_attribute = ExpenseAttribute.objects.filter(workspace_id=1, value='Electro wizard').first()

        assert expense_attribute.active == True

        mapping = Mapping.objects.filter(destination_id=destination_attribute.id).first()

        pre_run_expense_attribute_disabled_count = ExpenseAttribute.objects.filter(workspace_id=1, active=False, attribute_type='PROJECT').count()

        assert pre_run_expense_attribute_disabled_count == 4

        # This confirms that mapping is present and both expense_attribute and destination_attribute are active
        assert mapping.source_id == expense_attribute.id

        project.trigger_import()

        destination_attribute = DestinationAttribute.objects.filter(workspace_id=1, value='Electro wizard').first()
        
        assert destination_attribute.active == False

        expense_attribute = ExpenseAttribute.objects.filter(workspace_id=1, value='Electro wizard').first()

        assert expense_attribute.active == False

        post_run_expense_attribute_disabled_count = ExpenseAttribute.objects.filter(workspace_id=1, active=False, attribute_type='PROJECT').count()

        assert post_run_expense_attribute_disabled_count ==  pre_run_expense_attribute_disabled_count + destination_attributes_data['create_new_auto_create_projects_expense_attributes_4'][0]['count']


    #not re-enable case for project import
    with mock.patch('fyle.platform.apis.v1beta.admin.Projects.list_all') as mock_call:
        mocker.patch(
            'sageintacctsdk.apis.Projects.count',
            return_value=18
        )
        mocker.patch(
            'sageintacctsdk.apis.Projects.get_all',
            return_value=destination_attributes_data['create_new_auto_create_projects_destination_attributes_re_enable_case']
        )
        mocker.patch(
            'fyle_integrations_platform_connector.apis.Projects.post_bulk',
            return_value=[]
        )
        mock_call.side_effect = [
            destination_attributes_data['create_new_auto_create_projects_expense_attributes_3'],
            destination_attributes_data['create_new_auto_create_projects_expense_attributes_3'] 
        ]

        pre_run_destination_attribute_count = DestinationAttribute.objects.filter(workspace_id=1, attribute_type = 'PROJECT', active=False).count()
        
        assert pre_run_destination_attribute_count == 2

        pre_run_expense_attribute_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'PROJECT', active=False).count()

        assert pre_run_expense_attribute_count == 4

        project.trigger_import()

        post_run_destination_attribute_count = DestinationAttribute.objects.filter(workspace_id=1, attribute_type = 'PROJECT', active=False).count()

        assert post_run_destination_attribute_count == pre_run_destination_attribute_count - 2

        post_run_expense_attribute_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'PROJECT', active=False).count()

        assert pre_run_expense_attribute_count == post_run_expense_attribute_count


    
    # Not creating the schedule part due to time diff
    current_time = datetime.now()
    sync_after = current_time.replace(tzinfo=timezone.utc)
    project.sync_after = sync_after

    import_log = ImportLog.objects.filter(workspace_id=1).first()
    import_log.status = 'COMPLETE'
    import_log.attribute_type = 'PROJECT'
    import_log.total_batches_count = 10
    import_log.processed_batches_count = 10
    import_log.error_log = []
    import_log.save()

    import_log = ImportLog.objects.filter(workspace_id=1).first()

    response = project.trigger_import()

    import_log_post_run = ImportLog.objects.filter(workspace_id=1).first()

    assert response == None
    assert import_log.status == import_log_post_run.status
    assert import_log.total_batches_count == import_log_post_run.total_batches_count

    # not creating the schedule due to a schedule running already
    project.sync_after = None

    import_log = ImportLog.objects.filter(workspace_id=1).first()
    import_log.status = 'IN_PORGRESS'
    import_log.total_batches_count = 8
    import_log.processed_batches_count = 3
    import_log.save()

    response = project.trigger_import()

    assert response == None
    assert import_log.status == 'IN_PORGRESS'
    assert import_log.total_batches_count != 0
    assert import_log.processed_batches_count != 0

    # Setting import_log to COMPLETE since there are no destination_attributes
    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Projects.list_all',
        return_value=[]
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.count',
        return_value=0
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.get_all',
        return_value=[]
    )

    Mapping.objects.filter(workspace_id=1, source_type='PROJECT', destination_type='PROJECT').delete()
    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT').delete()
    project.sync_after = None

    response = project.trigger_import()

    import_log = ImportLog.objects.filter(workspace_id=1, attribute_type='PROJECT').first()
    assert import_log.status == 'COMPLETE'
    assert import_log.total_batches_count == 0
    assert import_log.processed_batches_count == 0
    assert response == None

def test_expense_attributes_sync_after(db):
    project = Project(1, 'PROJECT', None)

    current_time = datetime.now() - timedelta(minutes=300)
    sync_after = current_time.replace(tzinfo=timezone.utc)
    project.sync_after = sync_after

    expense_attributes = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT')[0:100]

    assert expense_attributes.count() == 100

    paginated_expense_attribute_values = []

    for expense_attribute in expense_attributes:
        expense_attribute.updated_at = datetime.now().replace(tzinfo=timezone.utc)
        expense_attribute.save()
        paginated_expense_attribute_values.append(expense_attribute.value)


    filters = project.construct_attributes_filter('PROJECT', paginated_expense_attribute_values)

    expense_attributes = ExpenseAttribute.objects.filter(**filters)

    assert expense_attributes.count() == 100

def test_resolve_expense_attribute_errors(db):
    workspace_id = 1
    category = Category(1, 'EXPENSE_TYPE', None)

    # deleting all the Error objects
    Error.objects.filter(workspace_id=workspace_id).delete()

    # getting the expense_attribute
    source_category = ExpenseAttribute.objects.filter(
        id=106,
        workspace_id=1,
        attribute_type='CATEGORY'
    ).first()

    category_mapping_count = CategoryMapping.objects.filter(workspace_id=1, source_category_id=source_category.id).count()

    # category mapping is not present
    assert category_mapping_count == 0

    error = Error.objects.create(
        workspace_id=workspace_id,
        expense_attribute=source_category,
        type='CATEGORY_MAPPING',
        error_title=source_category.value,
        error_detail='Category mapping is missing',
        is_resolved=False
    )

    assert Error.objects.get(id=error.id).is_resolved == False

    destination_attribute = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='EXPENSE_TYPE').first()

    # creating the category mapping in bulk mode to avoid setting the is_resolved flag to true by signal
    category_list = []
    category_list.append(
        CategoryMapping(
        workspace_id=1,
        source_category_id=source_category.id,
        destination_expense_head_id=destination_attribute.id
    ))
    CategoryMapping.objects.bulk_create(category_list)

    category.resolve_expense_attribute_errors()
    assert Error.objects.get(id=error.id).is_resolved == True
