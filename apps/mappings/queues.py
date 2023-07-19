# TODO : Fix this file . Pls dont check the content of this file
import time

from django_q.tasks import Chain

from fyle_accounting_mappings.models import MappingSetting
from apps.workspaces.models import Configuration


IMPORT_TASK_TARGET_MAP = {
    'PROJECT': 'Project.trigger_import',
    'COST_CENTER': 'CostCenter.trigger_import',
    'TAX_GROUP': 'TaxGroup.trigger_import',
}


def chain_import_fields_to_fyle(workspace_id):
    mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id, import_to_fyle=True)
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    chain = Chain()

    if configuration.import_vendors_as_merchants:
        chain.append(
            'apps.mappings.imported_task.Merchant',
            workspace_id
        )
    
    for mapping_setting in mapping_settings:
        if mapping_setting.is_custom:
            chain.append(
                'apps.mappings.imported_task.ExpenseCustomField',
                workspace_id,
                mapping_setting.destination_field,
                mapping_setting.source_field
            )
        else:
            chain.append(
                'apps.mappings.imported_task.{}'.format(IMPORT_TASK_TARGET_MAP[mapping_setting.source_field]),
                workspace_id,
                mapping_setting.destination_field
            )

    if chain.length() > 0:
        chain.run()
