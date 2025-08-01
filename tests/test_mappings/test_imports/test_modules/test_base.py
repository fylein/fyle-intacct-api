from unittest import mock
from datetime import datetime, timezone, timedelta

from fyle_accounting_mappings.models import (
    Mapping,
    CategoryMapping,
    ExpenseAttribute,
    DestinationAttribute
)
from fyle_integrations_platform_connector import PlatformConnector

from apps.tasks.models import Error
from fyle_integrations_imports.models import ImportLog
from apps.sage_intacct.utils import SageIntacctConnector
from fyle_integrations_imports.modules.projects import Project
from fyle_integrations_imports.modules.categories import Category
from apps.workspaces.models import FyleCredential, SageIntacctCredential, Workspace
from fyle_integrations_imports.modules.base import Base

from .fixtures import data as destination_attributes_data
from .helpers import get_platform_connection
from apps.mappings.constants import SYNC_METHODS

from unittest.mock import patch, MagicMock


def test_sync_destination_attributes(mocker, db):
    """
    Test sync destination attributes
    """
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Projects.get_all_generator',
        return_value=destination_attributes_data['get_projects_destination_attributes']
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.count',
        return_value=18
    )

    project_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert project_count == 16

    project = Project(workspace_id, 'PROJECT', None, mock.Mock(), [SYNC_METHODS['PROJECT']], True)
    project.sync_destination_attributes()

    new_project_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert new_project_count == 16


def test_sync_expense_atrributes(mocker, db):
    """
    Test sync expense attributes
    """
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credentials.workspace.fyle_org_id = 'orqjgyJ21uge'
    fyle_credentials.workspace.save()
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    mocker.patch(
        'fyle.platform.apis.v1.admin.Projects.list_all',
        return_value=[]
    )

    projects_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert projects_count == 1244

    project = Project(workspace_id, 'PROJECT', None, mock.Mock(), [SYNC_METHODS['PROJECT']], True)
    project.sync_expense_attributes(platform)

    projects_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert projects_count == 1244

    mocker.patch(
        'fyle.platform.apis.v1.admin.Projects.list_all',
        return_value=destination_attributes_data['create_new_auto_create_projects_expense_attributes_0']
    )
    project.sync_expense_attributes(platform)

    projects_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert projects_count == 1244 + destination_attributes_data['create_new_auto_create_projects_expense_attributes_0'][0]['count']


def test_remove_duplicates(db):
    """
    Test remove duplicates
    """
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

    base = Base(1, 'EMPLOYEE', 'EMPLOYEE', 'employees', None, mock.Mock(), ['employees'])

    attributes = base.remove_duplicate_attributes(attributes)
    assert len(attributes) == 55


def test_get_platform_class(db):
    """
    Test get platform class
    """
    base = Base(1, 'PROJECT', 'PROJECT', 'projects', None, mock.Mock(), [SYNC_METHODS['PROJECT']])
    platform = get_platform_connection(1)

    assert base.get_platform_class(platform) == platform.projects

    base = Base(1, 'CATEGORY', 'ACCOUNT', 'categories', None, mock.Mock(), [SYNC_METHODS['ACCOUNT']])
    assert base.get_platform_class(platform) == platform.categories

    base = Base(1, 'COST_CENTER', 'DEPARTMENT', 'cost_centers', None, mock.Mock(), [SYNC_METHODS['DEPARTMENT']])
    assert base.get_platform_class(platform) == platform.cost_centers


def test_construct_attributes_filter(db):
    """
    Test construct attributes filter
    """
    base = Base(1, 'PROJECT', 'PROJECT', 'projects', None, mock.Mock(), [SYNC_METHODS['PROJECT']])

    assert base.construct_attributes_filter('PROJECT') == {'attribute_type': 'PROJECT', 'workspace_id': 1, 'active': True}

    date_string = '2023-08-06 12:50:05.875029'
    sync_after = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S.%f')

    base = Base(1, 'CATEGORY', 'ACCOUNT', 'categories', sync_after, mock.Mock(), [SYNC_METHODS['ACCOUNT']])
    assert base.construct_attributes_filter('CATEGORY', is_auto_sync_enabled=True) == {'attribute_type': 'CATEGORY', 'workspace_id': 1, 'updated_at__gte': sync_after}

    paginated_destination_attribute_values = ['Mobile App Redesign', 'Platform APIs', 'Fyle NetSuite Integration', 'Fyle Sage Intacct Integration', 'Support Taxes', 'T&M Project with Five Tasks', 'Fixed Fee Project with Five Tasks', 'General Overhead', 'General Overhead-Current', 'Youtube proj', 'Integrations', 'Yujiro', 'Pickle']

    base = Base(1, 'COST_CENTER', 'COST_CENTER', 'cost_centers', sync_after, mock.Mock(), [SYNC_METHODS['PROJECT']])
    assert base.construct_attributes_filter('COST_CENTER', paginated_destination_attribute_values=paginated_destination_attribute_values, is_destination_type=True, is_auto_sync_enabled=True) == {'attribute_type': 'COST_CENTER', 'workspace_id': 1, 'updated_at__gte': sync_after, 'value__in': paginated_destination_attribute_values}


def test_auto_create_destination_attributes(mocker, db):
    """
    Test auto create destination attributes
    """
    sage_creds = SageIntacctCredential.objects.get(workspace_id=1)
    sage_connection = SageIntacctConnector(sage_creds, 1)
    project = Project(1, 'PROJECT', None, sage_connection, [SYNC_METHODS['PROJECT']], True)
    project.sync_after = None

    Workspace.objects.filter(id=1).update(fyle_org_id='orqjgyJ21uge')
    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(workspace_id=1, source_type='PROJECT', destination_type='PROJECT').delete()
    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT').delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT').delete()

    # create new case for projects import
    with mock.patch('fyle.platform.apis.v1.admin.Projects.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.Projects.post_bulk',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.Projects.count',
            return_value=18
        )
        mocker.patch(
            'sageintacctsdk.apis.Projects.get_all_generator',
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

        assert expense_attributes_count == 5

        mappings_count = Mapping.objects.filter(workspace_id=1, source_type='PROJECT', destination_type='PROJECT').count()

        assert mappings_count == 2

    # disable case for project import
    with mock.patch('fyle.platform.apis.v1.admin.Projects.list_all') as mock_call:
        mocker.patch(
            'sageintacctsdk.apis.Projects.count',
            return_value=18
        )
        mocker.patch(
            'sageintacctsdk.apis.Projects.get_all_generator',
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

        assert pre_run_expense_attribute_disabled_count == 1

        # This confirms that mapping is present and both expense_attribute and destination_attribute are active
        assert mapping.source_id == expense_attribute.id

        project.trigger_import()

        destination_attribute = DestinationAttribute.objects.filter(workspace_id=1, value='Electro wizard').first()

        assert destination_attribute.active == False

        expense_attribute = ExpenseAttribute.objects.filter(workspace_id=1, value='Electro wizard').first()

        assert expense_attribute.active == False

        post_run_expense_attribute_disabled_count = ExpenseAttribute.objects.filter(workspace_id=1, active=False, attribute_type='PROJECT').count()

        assert post_run_expense_attribute_disabled_count == 3

    # not re-enable case for project import
    with mock.patch('fyle.platform.apis.v1.admin.Projects.list_all') as mock_call:
        mocker.patch(
            'sageintacctsdk.apis.Projects.count',
            return_value=18
        )
        mocker.patch(
            'sageintacctsdk.apis.Projects.get_all_generator',
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

        assert pre_run_destination_attribute_count == 7

        pre_run_expense_attribute_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'PROJECT', active=False).count()

        assert pre_run_expense_attribute_count == 3

        project.trigger_import()

        post_run_destination_attribute_count = DestinationAttribute.objects.filter(workspace_id=1, attribute_type = 'PROJECT', active=False).count()

        assert post_run_destination_attribute_count == pre_run_destination_attribute_count - 2

        post_run_expense_attribute_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'PROJECT', active=False).count()

        assert post_run_expense_attribute_count == 2

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
        'fyle.platform.apis.v1.admin.Projects.list_all',
        return_value=[]
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.count',
        return_value=0
    )
    mocker.patch(
        'sageintacctsdk.apis.Projects.get_all_generator',
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
    """
    Test expense attributes sync after
    """
    project = Project(1, 'PROJECT', None, mock.Mock(), [SYNC_METHODS['PROJECT']], True)

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
    """
    Test resolve expense attribute errors
    """
    workspace_id = 1
    category = Category(1, 'EXPENSE_TYPE', None, mock.Mock(), [SYNC_METHODS['EXPENSE_TYPE']], True, False, [], True)

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
        )
    )
    CategoryMapping.objects.bulk_create(category_list)

    category.resolve_expense_attribute_errors()
    assert Error.objects.get(id=error.id).is_resolved == False


def test_create_disable_attributes(mocker, db):
    """
    Test create disable attributes
    """
    mocker.patch(
        'sageintacctsdk.apis.Projects.get_all_generator',
        return_value=destination_attributes_data['create_new_auto_create_projects_destination_attributes_active']
    )

    mocker.patch(
        'sageintacctsdk.apis.Projects.count',
        return_value=13
    )

    project = Project(1, 'PROJECT', None, mock.Mock(), [SYNC_METHODS['PROJECT']], True)
    project.sync_after = None
    workspace_id = 1

    Workspace.objects.filter(id=1).update(fyle_org_id='orqjgyJ21uge')
    # delete all destination attributes, expense attributes and mappings
    Mapping.objects.filter(workspace_id=1, source_type='PROJECT', destination_type='PROJECT').delete()
    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT').delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type='PROJECT').delete()

    intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sage_intacct_connection = SageIntacctConnector(credentials_object=intacct_credentials, workspace_id=workspace_id)

    sage_intacct_connection.sync_projects()

    new_projects = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert new_projects == 13

    new_projects = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT', active=True).count()
    assert new_projects == 13

    project = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT', value='Mobile App Redesign').first()
    assert project.active == True

    mocker.patch(
        'sageintacctsdk.apis.Projects.get_all_generator',
        return_value=destination_attributes_data['create_new_auto_create_projects_destination_attributes_inactive_active']
    )

    sage_intacct_connection.sync_projects()
    project = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT', value='Mobile App Redesign').first()
    assert project.active == False

    new_projects = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').count()
    assert new_projects == 14

    new_projects = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT', active=True).count()
    assert new_projects == 13


def test_create_ccc_category_mappings_called(mocker):
    """
    Test create ccc category mappings not called
    """
    # Patch bulk_create_ccc_category_mappings
    bulk_create_mock = mocker.patch('fyle_accounting_mappings.models.CategoryMapping.bulk_create_ccc_category_mappings')
    # Patch Configuration.objects.filter
    config_filter_mock = mocker.patch('apps.workspaces.models.Configuration.objects.filter')

    # Condition not met
    config = MagicMock()
    config.reimbursable_expenses_object = 'BILL'
    config.corporate_credit_card_expenses_object = 'BILL'
    config_filter_mock.return_value.first.return_value = config
    base = Base(1, 'CATEGORY', 'CATEGORY', 'categories', None, mock.Mock(), [SYNC_METHODS['ACCOUNT']])
    base.create_ccc_mappings()
    bulk_create_mock.assert_called_once()


@patch('fyle_integrations_imports.modules.base.ImportLog')
def test_update_import_log_post_import_else(import_log_mock):
    """
    Test update import log post import else
    """
    # is_last_batch False
    base = Base(1, 'CATEGORY', 'CATEGORY', 'categories', None, mock.Mock(), [SYNC_METHODS['ACCOUNT']])
    import_log = MagicMock()
    import_log.processed_batches_count = 0
    base.update_import_log_post_import(False, import_log)
    import_log.save.assert_called_once()
    assert import_log.processed_batches_count == 1


@patch('fyle_integrations_imports.modules.base.ImportLog.objects.get_or_create')
@patch('fyle_integrations_imports.modules.base.Base.import_destination_attribute_to_fyle')
def test_check_import_log_and_start_import_in_progress(import_dest_mock, get_or_create_mock):
    """
    Test check import log and start import in progress
    """
    # import_log in progress, not created
    import_log = MagicMock()
    import_log.status = 'IN_PROGRESS'
    is_created = False
    get_or_create_mock.return_value = (import_log, is_created)
    base = Base(1, 'CATEGORY', 'CATEGORY', 'categories', None, mock.Mock(), [SYNC_METHODS['ACCOUNT']])
    base.check_import_log_and_start_import()
    import_dest_mock.assert_not_called()


@patch('fyle_integrations_imports.modules.base.ImportLog.objects.get_or_create')
@patch('fyle_integrations_imports.modules.base.Base.import_destination_attribute_to_fyle')
def test_check_import_log_and_start_import_sync_after(import_dest_mock, get_or_create_mock):
    """
    Test check import log and start import sync after
    """
    # sync_after in the future
    import_log = MagicMock()
    import_log.status = 'COMPLETE'
    is_created = True
    get_or_create_mock.return_value = (import_log, is_created)
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    base = Base(1, 'CATEGORY', 'CATEGORY', 'categories', future_time, mock.Mock(), [SYNC_METHODS['ACCOUNT']])
    base.check_import_log_and_start_import()
    import_dest_mock.assert_not_called()
