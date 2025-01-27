from django_q.tasks import Chain

from fyle_accounting_mappings.models import MappingSetting

from apps.mappings.models import ImportLog
from apps.workspaces.models import Configuration
from apps.fyle.models import DependentFieldSetting
from apps.mappings.helpers import is_project_sync_allowed


def chain_import_fields_to_fyle(workspace_id: int) -> None:
    """
    Chain import fields to Fyle
    :param workspace_id: Workspace Id
    :return: None
    """
    mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id, import_to_fyle=True)
    configuration = Configuration.objects.get(workspace_id=workspace_id)
    dependent_fields = DependentFieldSetting.objects.filter(workspace_id=workspace_id, is_import_enabled=True).first()

    import_code_fields = configuration.import_code_fields

    project_import_log = ImportLog.objects.filter(workspace_id=workspace_id, attribute_type='PROJECT').first()
    # We'll only sync PROJECT and Dependent Fields together in one run
    is_sync_allowed = is_project_sync_allowed(project_import_log)

    custom_field_mapping_settings = []
    project_mapping = None

    for setting in mapping_settings:
        if setting.is_custom:
            custom_field_mapping_settings.append(setting)
        if setting.source_field == 'PROJECT':
            project_mapping = setting

    chain = Chain()

    if configuration.import_tax_codes:
        chain.append(
            'apps.mappings.imports.tasks.trigger_import_via_schedule',
            workspace_id,
            'TAX_DETAIL',
            'TAX_GROUP',
            q_options={'cluster': 'import'}
        )

    if configuration.import_vendors_as_merchants:
        chain.append(
            'apps.mappings.imports.tasks.trigger_import_via_schedule',
            workspace_id,
            'VENDOR',
            'MERCHANT',
            q_options={'cluster': 'import'}
        )

    if configuration.import_categories:
        if configuration.reimbursable_expenses_object == 'EXPENSE_REPORT' or \
            configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
            destination_field = 'EXPENSE_TYPE'
        else:
            destination_field = 'ACCOUNT'

        chain.append(
            'apps.mappings.imports.tasks.trigger_import_via_schedule',
            workspace_id,
            destination_field,
            'CATEGORY',
            False,
            True if destination_field in import_code_fields else False,
            q_options={'cluster': 'import'}
        )

    for mapping_setting in mapping_settings:
        if mapping_setting.source_field in ['PROJECT', 'COST_CENTER']:
            chain.append(
                'apps.mappings.imports.tasks.trigger_import_via_schedule',
                workspace_id,
                mapping_setting.destination_field,
                mapping_setting.source_field,
                False,
                True if mapping_setting.destination_field in import_code_fields else False,
                q_options={'cluster': 'import'}
            )

    for custom_fields_mapping_setting in custom_field_mapping_settings:
        chain.append(
            'apps.mappings.imports.tasks.trigger_import_via_schedule',
            workspace_id,
            custom_fields_mapping_setting.destination_field,
            custom_fields_mapping_setting.source_field,
            True,
            True if custom_fields_mapping_setting.destination_field in import_code_fields else False,
            q_options={'cluster': 'import'}
        )

    if project_mapping and dependent_fields and is_sync_allowed:
        chain.append(
            'apps.sage_intacct.dependent_fields.import_dependent_fields_to_fyle',
            workspace_id,
            q_options={'cluster': 'import', 'timeout': 27000}
        )

    if chain.length() > 0:
        chain.run()
