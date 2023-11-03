from django_q.tasks import Chain
from fyle_accounting_mappings.models import MappingSetting
from apps.workspaces.models import Configuration
from apps.mappings.imports.queues import chain_import_fields_to_fyle
from apps.workspaces.models import SageIntacctCredential
from django.utils.module_loading import import_string

SYNC_METHODS = {
    'LOCATION': 'locations',
    'PROJECT': 'projects',
    'DEPARTMENT': 'departments',
    'VENDOR': 'vendors',
    'CLASS': 'classes',
    'TAX_DETAIL': 'tax_details',
    'ITEM': 'items',
    'CUSTOMER': 'customers',
    'COST_TYPE': 'cost_types',
    'EXPENSE_TYPE': 'expense_types',
    'ACCOUNT': 'accounts',
}

def construct_task_settings_payload(workspace_id):
    """
    Chain import fields to Fyle
    :param workspace_id: Workspace Id
    """
    mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id, import_to_fyle=True)
    custom_field_mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id, is_custom=True, import_to_fyle=True)
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=workspace_id)
    sdk_connection = import_string('apps.sage_intacct.utils.SageIntacctConnector')(sage_intacct_credentials, workspace_id)

    task_settings = {
        'import_tax_codes': {
            'destination_field': '',
            'destination_sync_method': '',
            'import': False,
        },
        'import_vendors_as_merchants': {
            'destination_field': '',
            'destination_sync_method': '',
            'import': False,
        },
        'import_categories': {
            'destination_field': '',
            'destination_sync_method': '',
            'import': False,
        },
        'mapping_settings': [],
        'sdk_connection': sdk_connection,
    }

    if configuration.import_tax_codes:
        task_settings['import_tax_codes'] = {
            'destination_field': 'TAX_DETAIL',
            'destination_sync_method': SYNC_METHODS['TAX_DETAIL'],
            'import': True,
        }

    if configuration.import_vendors_as_merchants:
        task_settings['import_vendors_as_merchants'] = {
            'destination_field': 'VENDOR',
            'destination_sync_method': SYNC_METHODS['VENDOR'],
            'import': True,
        }

    if configuration.import_categories:
        if configuration.reimbursable_expenses_object == 'EXPENSE_REPORT' or \
            configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
            destination_field = 'EXPENSE_TYPE'
        else:
            destination_field = 'ACCOUNT'
        
        task_settings['import_categories'] = {
            'destination_field': destination_field,
            'destination_sync_method': SYNC_METHODS[destination_field],
            'import': True,
        }

    for mapping_setting in mapping_settings:
        if mapping_setting.source_field in ['PROJECT', 'COST_CENTER']:
            task_settings['mapping_settings'].append({
                'source_field': mapping_setting.source_field,
                'destination_field': mapping_setting.destination_field,
                'destination_sync_method': SYNC_METHODS[mapping_setting.destination_field],
                'is_custom': False,
            })

    for custom_fields_mapping_setting in custom_field_mapping_settings:
        task_settings['mapping_settings'].append({
            'source_field': custom_fields_mapping_setting.source_field,
            'destination_field': custom_fields_mapping_setting.destination_field,
            'destination_sync_method': SYNC_METHODS[mapping_setting.destination_field],
            'is_custom': True,
        })

    chain_import_fields_to_fyle(workspace_id, task_settings)
