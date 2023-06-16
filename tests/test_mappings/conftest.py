import pytest
from fyle_accounting_mappings.models import MappingSetting, DestinationAttribute

from apps.fyle.models import DependentFieldSetting
from apps.sage_intacct.models import CostType


@pytest.fixture
def create_mapping_setting(db):
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
    workspace_id = 1
    CostType.objects.update_or_create(
        workspace_id=workspace_id,
        defaults={
            'record_number': 34234,
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
