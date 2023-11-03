from django_q.tasks import Chain
from fyle_accounting_mappings.models import MappingSetting
from apps.workspaces.models import Configuration


# task_settings = {
#     'import_tax_codes': {
#         'destination_field': '',
#         'destination_sync_method': '',
#         'import': False,
#     },
#     'import_vendors_as_merchants': {
#         'destination_field': '',
#         'destination_sync_method': '',
#         'import': False,
#     },
#     'import_categories': {
#         'destination_field': '',
#         'destination_sync_method': '',
#         'import': False,
#     },
#     'mapping_settings': [
#         {
#             'source_field': 'PROJECT',
#             'destination_field': 'CUSTOMER',
#             'destination_sync_method': 'customers',
#             'is_custom': False,
#         },
#         {
#             'source_field': 'KLASS',
#             'destination_field': 'CLASS',
#             'destination_sync_method': 'classes',
#             'is_custom': True,
#         },
#     ],
#     'sdk_connection': sdk_connection,
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
            tasks_settings['import_tax_codes']['destination_sync_method']
        )

    if tasks_settings['import_vendors_as_merchants']['import']:
        chain.append(
            'apps.mappings.imports.tasks.trigger_import_via_schedule',
            workspace_id,
            'VENDOR',
            'MERCHANT',
            tasks_settings['sdk_connection'],
            tasks_settings['import_vendors_as_merchants']['destination_sync_method']
        )

    if tasks_settings['import_categories']['import']:
        chain.append(
            'apps.mappings.imports.tasks.trigger_import_via_schedule',
            workspace_id,
            tasks_settings['import_categories']['destination_field'],
            'CATEGORY',
            tasks_settings['sdk_connection'],
            tasks_settings['import_categories']['destination_sync_method']
        )

    if tasks_settings['mapping_settings']:
        for mapping_setting in tasks_settings['mapping_settings']:
            if mapping_setting.source_field in ['PROJECT', 'COST_CENTER']:
                chain.append(
                    'apps.mappings.imports.tasks.trigger_import_via_schedule',
                    workspace_id,
                    mapping_setting['destination_field'],
                    mapping_setting['source_field'],
                    tasks_settings['sdk_connection'],
                    mapping_setting['destination_sync_method'],
                    mapping_setting['is_custom']
                )

    if chain.length() > 0:
        chain.run()
