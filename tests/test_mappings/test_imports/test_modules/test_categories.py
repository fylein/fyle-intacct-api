from unittest import mock
from apps.mappings.imports.modules.categories import Category, disable_categories
from fyle_accounting_mappings.models import (
    DestinationAttribute,
    ExpenseAttribute,
    CategoryMapping
)
from fyle_integrations_platform_connector import PlatformConnector
from apps.workspaces.models import (
    FyleCredential,
    Configuration,
    Workspace
)
from .fixtures import category_data


def test_sync_destination_attributes_categories(mocker, db):
    workspace_id = 1

    mocker.patch(
        'sageintacctsdk.apis.Accounts.get_all',
        return_value=category_data['get_categories_destination_attributes_account']
    )

    account_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='ACCOUNT').count()
    assert account_count == 170

    category = Category(workspace_id, 'ACCOUNT', None)
    category.sync_destination_attributes('ACCOUNT')

    new_account_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='ACCOUNT').count()
    assert new_account_count == account_count + len(category_data['get_categories_destination_attributes_account'])

    mocker.patch(
        'sageintacctsdk.apis.ExpenseTypes.get_all',
        return_value=category_data['get_categories_destination_attributes_expense_type']
    )

    expense_type_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='EXPENSE_TYPE').count()
    assert expense_type_count == 8

    category = Category(workspace_id, 'EXPENSE_TYPE', None)
    category.sync_destination_attributes('EXPENSE_TYPE')

    new_expense_type_count = DestinationAttribute.objects.filter(workspace_id=workspace_id, attribute_type='EXPENSE_TYPE').count()
    assert new_expense_type_count == expense_type_count + len(category_data['get_categories_destination_attributes_expense_type'])


def test_sync_expense_atrributes(mocker, db):
    workspace_id = 1
    fyle_credentials = FyleCredential.objects.get(workspace_id=workspace_id)
    fyle_credentials.workspace.fyle_org_id = 'orwimNcVyYsp'
    fyle_credentials.workspace.save()
    platform = PlatformConnector(fyle_credentials=fyle_credentials)

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Categories.list_all',
        return_value=[]
    )

    category_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CATEGORY').count()
    assert category_count == 619

    category = Category(workspace_id, 'ACCOUNT', None)
    category.sync_expense_attributes(platform)

    category_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CATEGORY').count()
    assert category_count == 619

    mocker.patch(
        'fyle.platform.apis.v1beta.admin.Categories.list_all',
        return_value=category_data['create_new_auto_create_categories_expense_attributes_1']
    )

    category.sync_expense_attributes(platform)

    category_count = ExpenseAttribute.objects.filter(workspace_id=workspace_id, attribute_type='CATEGORY').count()
    # NOTE : we are not using category_data['..'][0]['count'] because some duplicates where present in the data
    assert category_count == 630

def test_auto_create_destination_attributes_categories(mocker, db):
    category = Category(1, 'EXPENSE_TYPE', None)
    category.sync_after = None

    Workspace.objects.filter(id=1).update(fyle_org_id='orwimNcVyYsp')

    # delete all destination attributes, expense attributes and mappings
    CategoryMapping.objects.filter(workspace_id=1).delete()
    DestinationAttribute.objects.filter(workspace_id=1, attribute_type='EXPENSE_TYPE').delete()
    ExpenseAttribute.objects.filter(workspace_id=1, attribute_type='CATEGORY').delete()

    # create new case for categories import
    with mock.patch('fyle.platform.apis.v1beta.admin.Categories.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.Categories.post_bulk',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.ExpenseTypes.get_all',
            return_value=category_data['create_new_auto_create_expense_type_destination_attributes']
        )
        mock_call.side_effect = [
            category_data['create_new_auto_create_categories_expense_attributes_0'],
            category_data['create_new_auto_create_categories_expense_attributes_1'] 
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type='CATEGORY').count()

        assert expense_attributes_count == 0

        mappings_count = CategoryMapping.objects.filter(workspace_id=1).count()
        
        assert mappings_count == 0

        category.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(attribute_type='CATEGORY').count()

        assert expense_attributes_count == 30

        mappings_count = CategoryMapping.objects.filter(workspace_id=1).count()
        
        assert mappings_count == 12


    # disable case for categories import
    with mock.patch('fyle.platform.apis.v1beta.admin.Categories.list_all') as mock_call:
        mocker.patch(
            'sageintacctsdk.apis.ExpenseTypes.get_all',
            return_value=category_data['create_new_auto_create_expense_type_destination_attributes_disable_case']
        )
        mocker.patch(
            'fyle_integrations_platform_connector.apis.Categories.post_bulk',
            return_value=[]
        )
        mock_call.side_effect = [
            category_data['create_new_auto_create_categories_expense_attributes_2'],
            category_data['create_new_auto_create_categories_expense_attributes_3'] 
        ]

        
        destination_attribute = DestinationAttribute.objects.filter(workspace_id=1, value='labhvam', attribute_type='EXPENSE_TYPE').first()
        
        assert destination_attribute.active == True

        expense_attribute = ExpenseAttribute.objects.filter(workspace_id=1, value='labhvam', attribute_type='CATEGORY').first()

        assert expense_attribute.active == True

        category_mapping = CategoryMapping.objects.filter(destination_expense_head_id=destination_attribute.id).first()

        pre_run_expense_attribute_disabled_count = ExpenseAttribute.objects.filter(workspace_id=1, active=False, attribute_type='CATEGORY').count()

        assert pre_run_expense_attribute_disabled_count == 0

        # This confirms that mapping is present and both expense_attribute and destination_attribute are active
        assert category_mapping.source_category_id == expense_attribute.id

        category.trigger_import()

        destination_attribute = DestinationAttribute.objects.filter(workspace_id=1, value='labhvam', attribute_type='EXPENSE_TYPE').first()
        
        assert destination_attribute.active == False

        expense_attribute = ExpenseAttribute.objects.filter(workspace_id=1, value='labhvam', attribute_type='CATEGORY').first()

        assert expense_attribute.active == False

        post_run_expense_attribute_disabled_count = ExpenseAttribute.objects.filter(workspace_id=1, active=False, attribute_type='CATEGORY').count()

        assert post_run_expense_attribute_disabled_count ==  pre_run_expense_attribute_disabled_count + 4


    #not re-enable case for project import
    with mock.patch('fyle.platform.apis.v1beta.admin.Categories.list_all') as mock_call:
        mocker.patch(
            'sageintacctsdk.apis.ExpenseTypes.get_all',
            return_value=category_data['create_new_auto_create_categories_destination_attributes_re_enable_case']
        )
        mocker.patch(
            'fyle_integrations_platform_connector.apis.Categories.post_bulk',
            return_value=[]
        )
        mock_call.side_effect = [
            category_data['create_new_auto_create_categories_expense_attributes_3'],
            category_data['create_new_auto_create_categories_expense_attributes_3'] 
        ]

        pre_run_destination_attribute_count = DestinationAttribute.objects.filter(workspace_id=1, attribute_type = 'EXPENSE_TYPE', active=False).count()
        
        assert pre_run_destination_attribute_count == 2

        pre_run_expense_attribute_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'CATEGORY', active=False).count()

        assert pre_run_expense_attribute_count == 4

        category.trigger_import()

        post_run_destination_attribute_count = DestinationAttribute.objects.filter(workspace_id=1, attribute_type = 'EXPENSE_TYPE', active=False).count()

        assert post_run_destination_attribute_count == pre_run_destination_attribute_count - 2

        post_run_expense_attribute_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type = 'CATEGORY', active=False).count()

        assert pre_run_expense_attribute_count == post_run_expense_attribute_count


    category = Category(1, 'ACCOUNT', None)
    category.sync_after = None

    # create new case for categories import for Accounts case
    with mock.patch('fyle.platform.apis.v1beta.admin.Categories.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.Categories.post_bulk',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.Accounts.get_all',
            return_value=[]
        )
        mock_call.side_effect = [
            [],
            [] 
        ]

        expense_attributes_count = ExpenseAttribute.objects.filter(workspace_id=1, attribute_type='CATEGORY').count()

        assert expense_attributes_count == 30

        mappings_count = CategoryMapping.objects.filter(workspace_id=1).count()
        
        assert mappings_count == 12

        category.trigger_import()

        expense_attributes_count = ExpenseAttribute.objects.filter(attribute_type='CATEGORY').count()

        assert expense_attributes_count == 30

        mappings_count = CategoryMapping.objects.filter(workspace_id=1).count()
        
        assert mappings_count == 13

    # for 3D mapping case 
    configuration = Configuration.objects.get(workspace_id=1)
    configuration.reimbursable_expenses_object = 'EXPENSE_REPORT'
    configuration.corporate_credit_card_expenses_object = 'BILL'
    configuration.save()

    with mock.patch('fyle.platform.apis.v1beta.admin.Categories.list_all') as mock_call:
        mocker.patch(
            'fyle_integrations_platform_connector.apis.Categories.post_bulk',
            return_value=[]
        )
        mocker.patch(
            'sageintacctsdk.apis.Accounts.get_all',
            return_value=[]
        )
        mock_call.side_effect = [
            [],
            [] 
        ]

        mappings_count = CategoryMapping.objects.filter(workspace_id=1, destination_account_id__isnull=True).count()
        
        assert mappings_count == 12

        category.trigger_import()

        mappings_count = CategoryMapping.objects.filter(workspace_id=1, destination_account_id__isnull=True).count()
        
        assert mappings_count == 0


def test_construct_fyle_payload(db):
    category = Category(1, 'EXPENSE_TYPE', None)

    # create new case
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='EXPENSE_TYPE')
    existing_fyle_attributes_map = {}
    is_auto_sync_status_allowed = category.get_auto_sync_permission()

    fyle_payload = category.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed
    )

    assert fyle_payload == category_data['create_fyle_category_payload_create_new_case']

    # disable case
    DestinationAttribute.objects.filter(
        workspace_id=1,
        attribute_type='EXPENSE_TYPE',
        value__in=['Internet','Meals']
    ).update(active=False)

    ExpenseAttribute.objects.filter(
        workspace_id=1,
        attribute_type='CATEGORY',
        value__in=['Internet','Meals']
    ).update(active=True)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=1, attribute_type='EXPENSE_TYPE')

    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes]
    existing_fyle_attributes_map = category.get_existing_fyle_attributes(paginated_destination_attribute_values)

    fyle_payload = category.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        is_auto_sync_status_allowed
    )

    assert fyle_payload == category_data['create_fyle_category_payload_create_disable_case']


def test_get_existing_fyle_attributes(
    db,
    add_expense_destination_attributes_1,
    add_expense_destination_attributes_2,
    add_configuration
):
    category = Category(98, 'ACCOUNT', None)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=98, attribute_type='ACCOUNT')
    paginated_destination_attributes_without_duplicates = category.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = category.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert existing_fyle_attributes_map == {'internet': '10091', 'meals': '10092'}

    # with code prepending
    category.prepend_code_to_name = True
    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=98, attribute_type='ACCOUNT', code__isnull=False)
    paginated_destination_attributes_without_duplicates = category.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = category.get_existing_fyle_attributes(paginated_destination_attribute_values)

    assert existing_fyle_attributes_map == {'123 sageintacct': '10095'}


def test_construct_fyle_payload_with_code(
    db,
    add_expense_destination_attributes_1,
    add_expense_destination_attributes_2,
    add_configuration
):
    category = Category(98, 'ACCOUNT', None, True)

    paginated_destination_attributes = DestinationAttribute.objects.filter(workspace_id=98, attribute_type='ACCOUNT')
    paginated_destination_attributes_without_duplicates = category.remove_duplicate_attributes(paginated_destination_attributes)
    paginated_destination_attribute_values = [attribute.value for attribute in paginated_destination_attributes_without_duplicates]
    existing_fyle_attributes_map = category.get_existing_fyle_attributes(paginated_destination_attribute_values)

    # already exists
    fyle_payload = category.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        True
    )

    assert fyle_payload == []

    # create new case
    existing_fyle_attributes_map = {}
    fyle_payload = category.construct_fyle_payload(
        paginated_destination_attributes,
        existing_fyle_attributes_map,
        True
    )

    assert fyle_payload == category_data["create_fyle_category_payload_with_code_create_new_case"]


def test_disable_categories(
    db,
    mocker,
    add_configuration
):
    workspace_id = 1

    categories_to_disable = {
        'destination_id': {
            'value': 'old_category',
            'updated_value': 'new_category',
            'code': 'old_category_code',
            'updated_code': 'old_category_code'
        }
    }

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='CATEGORY',
        display_name='Category',
        value='old_category',
        source_id='source_id',
        active=True
    )

    mock_platform = mocker.patch('apps.mappings.imports.modules.categories.PlatformConnector')
    bulk_post_call = mocker.patch.object(mock_platform.return_value.categories, 'post_bulk')

    disable_categories(workspace_id, categories_to_disable)

    assert bulk_post_call.call_count == 1

    categories_to_disable = {
        'destination_id': {
            'value': 'old_category_2',
            'updated_value': 'new_category',
            'code': 'old_category_code',
            'updated_code': 'new_category_code'
        }
    }

    disable_categories(workspace_id, categories_to_disable)
    assert bulk_post_call.call_count == 1

    # Test disable projects with code in naming
    import_settings = Configuration.objects.get(workspace_id=workspace_id)
    import_settings.import_code_fields = ['ACCOUNT']
    import_settings.save()

    ExpenseAttribute.objects.create(
        workspace_id=workspace_id,
        attribute_type='CATEGORY',
        display_name='Category',
        value='old_category_code old_category',
        source_id='source_id_123',
        active=True
    )

    categories_to_disable = {
        'destination_id': {
            'value': 'old_category',
            'updated_value': 'new_category',
            'code': 'old_category_code',
            'updated_code': 'old_category_code'
        }
    }

    payload = [{
        'name': 'old_category_code old_category',
        'code': 'destination_id',
        'is_enabled': False,
        'id': 'source_id_123'
    }]

    bulk_payload = disable_categories(workspace_id, categories_to_disable)
    assert bulk_payload == payload
