from datetime import datetime, timezone
from django.db.models import Q

from fyle_accounting_mappings.models import MappingSetting, ExpenseAttribute

from apps.mappings.models import ImportLog
from apps.workspaces.models import Configuration


class ImportSettingsTrigger:
    """
    All the post save actions of Import Settings API
    """
    def __init__(self, mapping_settings: list[dict], workspace_id: int):
        self.__mapping_settings = mapping_settings
        self.__workspace_id = workspace_id

    def __unset_auto_mapped_flag(self, current_mapping_settings: list[MappingSetting], new_mappings_settings: list[dict]) -> None:
        """
        Set the auto_mapped flag to false for the expense_attributes for the attributes
        whose mapping is changed.
        """
        changed_source_fields = []

        for new_setting in new_mappings_settings:
            destination_field = new_setting['destination_field']
            source_field = new_setting['source_field']
            current_setting = current_mapping_settings.filter(destination_field=destination_field).first()
            if current_setting and current_setting.source_field != source_field:
                changed_source_fields.append(source_field)

        ExpenseAttribute.objects.filter(workspace_id=self.__workspace_id, attribute_type__in=changed_source_fields).update(auto_mapped=False, updated_at=datetime.now(timezone.utc))

    def pre_save_mapping_settings(self) -> None:
        """
        Pre save action for mapping settings
        """
        mapping_settings = self.__mapping_settings

        current_mapping_settings = MappingSetting.objects.filter(workspace_id=self.__workspace_id).all()
        self.__unset_auto_mapped_flag(current_mapping_settings, mapping_settings)

    def post_save_mapping_settings(self, configurations_instance: Configuration) -> None:
        """
        Post save actions for mapping settings
        Here we need to clear out the data from the mapping-settings table for consecutive runs.
        """
        # We first need to avoid deleting mapping-settings that are always necessary.
        destination_fields = [
            'ACCOUNT',
            'CCC_ACCOUNT',
            'CHARGE_CARD_NUMBER',
            'EMPLOYEE',
            'EXPENSE_TYPE',
            'TAX_DETAIL',
            'VENDOR'
        ]

        # Here we are filtering out the mapping_settings payload and adding the destination-fields that are present in the payload
        # So that we avoid deleting them.
        for setting in self.__mapping_settings:
            if setting['destination_field'] not in destination_fields:
                destination_fields.append(setting['destination_field'])

        # Now that we have all the system necessary mapping-settings and the mapping-settings in the payload
        # This query will take care of deleting all the redundant mapping-settings that are not required.
        mapping_settings_to_delete = MappingSetting.objects.filter(
            ~Q(destination_field__in=destination_fields),
            workspace_id=self.__workspace_id
        ).all()

        if mapping_settings_to_delete:
            source_fields = [mapping_setting.source_field for mapping_setting in mapping_settings_to_delete]

            # Delete the import logs for the redundant mapping-settings
            ImportLog.objects.filter(
                workspace_id=self.__workspace_id, attribute_type__in=source_fields
            ).update(last_successful_run_at=None, updated_at=datetime.now(timezone.utc))

            # Delete the mapping settings
            mapping_settings_to_delete.delete()
