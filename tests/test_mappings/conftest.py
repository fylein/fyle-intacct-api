import pytest

from fyle_accounting_mappings.models import (
    MappingSetting,
    ExpenseAttribute,
    DestinationAttribute
)

from apps.sage_intacct.models import CostType
from apps.fyle.models import DependentFieldSetting
from apps.workspaces.models import Configuration, Workspace


@pytest.fixture
def create_mapping_setting(db):
    """
    Pytest fixture to create mapping setting
    """
    workspace_id = 1

    MappingSetting.objects.update_or_create(
        source_field='COST_CENTER',
        workspace_id=workspace_id,
        destination_field='COST_CENTER',
        defaults={
            'import_to_fyle': True,
            'is_custom': False
        }
    )

    DestinationAttribute.bulk_create_or_update_destination_attributes(
        [{'attribute_type': 'COST_CENTER', 'display_name': 'Cost center', 'value': 'sample', 'destination_id': '7b354c1c-cf59-42fc-9449-a65c51988335'}], 'COST_CENTER', 1, True
    )


@pytest.fixture
def create_dependent_field_setting(db):
    """
    Pytest fixture to create dependent field setting
    """
    created_field, _ = DependentFieldSetting.objects.update_or_create(
        workspace_id=1,
        defaults={
            'is_import_enabled': True,
            'project_field_id': 123,
            'cost_code_field_name': 'Cost Code',
            'cost_code_field_id': 456,
            'cost_type_field_name': 'Cost Type',
            'cost_type_field_id': 789
        }
    )

    return created_field


@pytest.fixture
def create_cost_type(db):
    """
    Pytest fixture to create cost type
    """
    workspace_id = 1
    CostType.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'record_number': '34234',
            'project_key': 34,
            'project_id': 'pro1',
            'project_name': 'pro',
            'task_key': 34,
            'task_id': 'task1',
            'task_name': 'task',
            'status': 'ACTIVE',
            'cost_type_id': 'cost1',
            'name': 'cost'
        }
    )


@pytest.fixture
def add_configuration(db):
    """
    Pytest fixture to add configuration to a workspace
    """
    workspace_id = [1, 98]
    for workspace_id in workspace_id:
        Configuration.objects.update_or_create(
            workspace_id=workspace_id,
            defaults={
                'reimbursable_expenses_object': 'EXPENSE REPORT',
                'corporate_credit_card_expenses_object': 'JOURNAL ENTRY'
            }
        )


@pytest.fixture
def add_project_mappings(db):
    """
    Pytest fixture to add project mappings to a workspace
    """
    workspace_ids = [
        1
    ]
    for workspace_id in workspace_ids:
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='Direct Mail Campaign',
            value='Direct Mail Campaign',
            destination_id='10064',
            detail='Sage Intacct Project - Direct Mail Campaign, Id - 10064',
            active=True
        )
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='Platform APIs',
            value='Platform APIs',
            destination_id='10081',
            detail='Sage Intacct Project - Platform APIs, Id - 10081',
            active=True
        )
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='DEPARTMENT',
            display_name='CRE Platform',
            value='CRE Platform',
            destination_id='10065',
            detail='Sage Intacct Project - CRE Platform, Id - 10065',
            active=True,
            code='123'
        )
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='DEPARTMENT',
            display_name='Integrations CRE',
            value='Integrations CRE',
            destination_id='10082',
            detail='Sage Intacct Project - Integrations CRE, Id - 10082',
            active=True,
            code='123'
        )
        ExpenseAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='CRE Platform',
            value='123 CRE Platform',
            source_id='10065',
            detail='Sage Intacct Project - 123 CRE Platform, Id - 10065',
            active=True
        )
        ExpenseAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='PROJECT',
            display_name='Integrations CRE',
            value='123 Integrations CRE',
            source_id='10082',
            detail='Sage Intacct Project - 123 Integrations CRE, Id - 10082',
            active=True
        )


@pytest.fixture()
def add_cost_type(db):
    """
    Pytest fixture to add cost category to a workspace
    """
    workspace_ids = [
        1
    ]
    for workspace_id in workspace_ids:
        CostType.objects.create(
            record_number='34234',
            project_id='10064',
            project_key='10064',
            project_name='Platform APIs',
            task_id='cost_code_id',
            task_name='Platform APIs',
            task_key='10064',
            name='API',
            cost_type_id='cost_category_id',
            status=True,
            workspace_id=workspace_id,
            is_imported=False
        )
        CostType.objects.create(
            record_number='34235',
            project_id='10081',
            project_key='10081',
            project_name='Direct Mail Campaign',
            task_id='cost_code_id',
            task_name='Direct Mail Campaign',
            task_key='10081',
            name='Mail',
            cost_type_id='cost_category_id',
            status=True,
            workspace_id=workspace_id,
            is_imported=False
        )
        CostType.objects.create(
            record_number='34236',
            project_id='10065',
            project_name='Integrations CRE',
            project_key='10065',
            task_id='cost_code_id_123',
            task_name='Integrations CRE',
            task_key='10065',
            name='Integrations',
            cost_type_id='cost_category_id_456',
            status=True,
            workspace_id=workspace_id,
            is_imported=False
        )
        CostType.objects.create(
            record_number='34237',
            project_id='10082',
            project_name='CRE Platform',
            project_key='10082',
            task_id='cost_code_id_545',
            task_name='CRE Platform',
            task_key='10082',
            name='CRE',
            cost_type_id='cost_category_id_583',
            status=True,
            workspace_id=workspace_id,
            is_imported=False
        )


@pytest.fixture()
def add_dependent_field_setting(db):
    """
    Pytest fixture to add dependent fields to a workspace
    """
    workspace_ids = [
        1
    ]

    for workspace_id in workspace_ids:
        DependentFieldSetting.objects.create(
            is_import_enabled=True,
            project_field_id=1,
            cost_code_field_name='Cost Code',
            cost_code_field_id=123,
            cost_code_placeholder='Select Cost Code',
            cost_type_field_name='Cost Category',
            cost_type_field_id=456,
            cost_type_placeholder='Select Cost Category',
            workspace_id=workspace_id
        )


@pytest.fixture()
def add_expense_destination_attributes_1():
    """
    Pytest fixture to add expense & destination attributes to a workspace
    """
    values = ['Internet', 'Meals']
    count = 0

    Workspace.objects.update_or_create(
        id=98,
        name='Test Workspace_98',
        fyle_org_id='12345'
    )

    for value in values:
        count += 1
        ExpenseAttribute.objects.create(
            workspace_id=98,
            attribute_type='CATEGORY',
            display_name='Category',
            value=value,
            source_id='1009{0}'.format(count),
            detail='Merchant - Platform APIs, Id - 1008',
            active=True
        )
        DestinationAttribute.objects.create(
            workspace_id=98,
            attribute_type='ACCOUNT',
            display_name='Account',
            value=value,
            destination_id=value,
            detail='Merchant - Platform APIs, Id - 10081',
            active=True
        )


@pytest.fixture()
def add_expense_destination_attributes_2():
    """
    Pytest fixture to add expense & destination attributes to a workspace
    """
    ExpenseAttribute.objects.create(
        workspace_id=98,
        attribute_type='CATEGORY',
        display_name='Category',
        value="123: SageIntacct",
        source_id='10095',
        detail='Merchant - Platform APIs, Id - 10085',
        active=True
    )

    DestinationAttribute.objects.create(
        workspace_id=98,
        attribute_type='ACCOUNT',
        display_name='Account',
        value="SageIntacct",
        destination_id='10085',
        detail='Merchant - Platform APIs, Id - 10085',
        active=True,
        code='123'
    )


@pytest.fixture()
def add_cost_center_mappings(db):
    """
    Pytest fixtue to add cost center mappings to a workspace
    """
    Workspace.objects.update_or_create(
        id=98,
        name='Test Workspace_1',
        fyle_org_id='12345'
    )

    workspace_ids = [
        1, 98
    ]
    for workspace_id in workspace_ids:
        ExpenseAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='COST_CENTER',
            display_name='Direct Mail Campaign',
            value='Direct Mail Campaign',
            source_id='10064',
            detail='Cost Center - Direct Mail Campaign, Id - 10064',
            active=True
        )
        ExpenseAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='COST_CENTER',
            display_name='Platform APIs',
            value='Platform APIs',
            source_id='10081',
            detail='Cost Center - Platform APIs, Id - 10081',
            active=True
        )

        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='COST_CENTER',
            display_name='Direct Mail Campaign',
            value='Direct Mail Campaign',
            destination_id='10064',
            detail='Cost Center - Direct Mail Campaign, Id - 10064',
            active=True
        )
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='COST_CENTER',
            display_name='Platform APIs',
            value='Platform APIs',
            destination_id='10081',
            detail='Cost Center - Platform APIs, Id - 10081',
            active=True
        )
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='DEPARTMENT',
            display_name='CRE Platform',
            value='CRE Platform',
            destination_id='10065',
            detail='Sage Intacct Department - CRE Platform, Id - 10065',
            active=True,
            code='123'
        )
        DestinationAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='DEPARTMENT',
            display_name='Integrations CRE',
            value='Integrations CRE',
            destination_id='10082',
            detail='Sage Intacct Department - Integrations CRE, Id - 10082',
            active=True,
            code='123'
        )
        ExpenseAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='COST_CENTER',
            display_name='CRE Platform',
            value='123: CRE Platform',
            source_id='10065',
            detail='Sage Intacct Cost_Center - 123 CRE Platform, Id - 10065',
            active=True
        )
        ExpenseAttribute.objects.create(
            workspace_id=workspace_id,
            attribute_type='COST_CENTER',
            display_name='Integrations CRE',
            value='123: Integrations CRE',
            source_id='10082',
            detail='Sage Intacct Cost_Center - 123 Integrations CRE, Id - 10082',
            active=True
        )
