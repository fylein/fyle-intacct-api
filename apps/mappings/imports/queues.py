from django_q.tasks import Chain
from fyle_accounting_mappings.models import MappingSetting
from apps.workspaces.models import Configuration


IMPORT_TASK_TARGET_MAP = {
    'PROJECT': 'trigger_projects_import_via_schedule',
    'CATEGORY': 'trigger_categories_import_via_schedule',
}


def chain_import_fields_to_fyle(workspace_id):
    """
    Chain import fields to Fyle
    :param workspace_id: Workspace Id
    """
    mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id, import_to_fyle=True)
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    chain = Chain()

    if configuration.import_categories:
        if configuration.reimbursable_expenses_object == 'EXPENSE_REPORT' or \
            configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
            destination_field = 'EXPENSE_TYPE'
        else:
            destination_field = 'ACCOUNT'

        chain.append(
            'apps.mappings.imports.tasks.{}'.format(IMPORT_TASK_TARGET_MAP['CATEGORY']),
            workspace_id,
            destination_field
        )

    for mapping_setting in mapping_settings:
        if mapping_setting.source_field in IMPORT_TASK_TARGET_MAP:
            chain.append(
                'apps.mappings.imports.tasks.{}'.format(IMPORT_TASK_TARGET_MAP[mapping_setting.source_field]),
                workspace_id,
                mapping_setting.destination_field
            )

    if chain.length() > 0:
        chain.run()
