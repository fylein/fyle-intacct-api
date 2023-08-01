from django_q.tasks import Chain

from fyle_accounting_mappings.models import MappingSetting
from apps.workspaces.models import Configuration


IMPORT_TASK_TARGET_MAP = {
    'PROJECT': 'projects.trigger_import_via_schedule',
    'COST_CENTER': 'cost_centers.trigger_import_via_schedule'
}


def chain_import_fields_to_fyle(workspace_id):
    mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id, import_to_fyle=True)
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    chain = Chain()
    print("""
          
          
          chain_import_fields_to_fyle
          
          
          
        """)

    # if configuration.import_vendors_as_merchants:
    #     chain.append(
    #         'apps.mappings.imported_task.Merchant.trigger_import',
    #         workspace_id
    #     )

    # if configuration.import_categories:
    #     chain.append(
    #         'apps.mappings.imported_task.Categories.trigger_import',
    #         workspace_id
    #     )   

    # if configuration.import_tax_codes:
    #     chain.append(
    #         'apps.mappings.imported_task.TaxGroup.trigger_import',
    #         workspace_id
    #     )

    for mapping_setting in mapping_settings:
        if mapping_setting.is_custom :
            chain.append(
                'apps.mappings.imported_task.ExpenseCustomField.trigger_import',
                workspace_id,
                mapping_setting.destination_field,
                mapping_setting.source_field
            )
        else:
            print("Inside else block")
            chain.append(
                'apps.mappings.imports.{}'.format(IMPORT_TASK_TARGET_MAP[mapping_setting.source_field]),
                workspace_id,
                mapping_setting.destination_field
            )

    if chain.length() > 0:
        chain.run()