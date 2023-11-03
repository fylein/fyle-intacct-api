from django_q.tasks import Chain
from fyle_accounting_mappings.models import MappingSetting
from apps.workspaces.models import Configuration


# task_settings = {
#   'import_tax_codes': {
#       'destination_field': 'TAX_DETAIL/TAX_CODE',
#       'import': True,
#   }
#   'import_vendors_as_merchants': True,
#   'import_categories': {
#       'import': True,
#       'destination_field': 'ACCOUNT/EXPENSE_TYPE' 
#   },
#   'mapping_settings': [
#       {
#           'source_field': 'PROJECT',
#           'destination_field': 'PROJECT',
#           'is_custom': False,
#       },
#       {
#           'source_field': 'COST_CENTER',
#           'destination_field': 'DEPARTMENT',
#           'is_custom': False,
#       },
#       {
#           'source_field': 'KLASS',
#           'destination_field': 'CLASS',
#           'is_custom': True,
#       },
#   ],
# }

def chain_import_fields_to_fyle(workspace_id, tasks_settings: dict):
    """
    Chain import fields to Fyle
    :param workspace_id: Workspace Id
    """
    chain = Chain()

    if tasks_settings['import_tax_codes']['import']:
        chain.append(
            'apps.mappings.imports.tasks.trigger_import_via_schedule',
            workspace_id,
            tasks_settings['import_tax_codes']['destination_field'],
            'TAX_GROUP',
            tasks_settings['sdk_connection'],
            
        )

    if tasks_settings['import_vendors_as_merchants']:
        chain.append(
            'apps.mappings.imports.tasks.trigger_import_via_schedule',
            workspace_id,
            'VENDOR',
            'MERCHANT'
        )

    if tasks_settings['import_categories']['import']:
        chain.append(
            'apps.mappings.imports.tasks.trigger_import_via_schedule',
            workspace_id,
            tasks_settings['import_categories']['destination_field'],
            'CATEGORY'
        )

    if tasks_settings['mapping_settings']:
        for mapping_setting in tasks_settings['mapping_settings']:
            if mapping_setting.source_field in ['PROJECT', 'COST_CENTER']:
                chain.append(
                    'apps.mappings.imports.tasks.trigger_import_via_schedule',
                    workspace_id,
                    mapping_setting['destination_field'],
                    mapping_setting['source_field'],
                    mapping_setting['is_custom']
                )

    if chain.length() > 0:
        chain.run()
