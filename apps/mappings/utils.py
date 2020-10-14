from typing import Dict

from apps.workspaces.models import WorkspaceGeneralSettings
from fyle_intacct_api.utils import assert_valid

from .models import GeneralMapping

class MappingUtils:
    def __init__(self, workspace_id):
        self.__workspace_id = workspace_id

    def create_or_update_general_mapping(self, general_mapping: Dict):
        """
        Create or update general mapping
        :param general_mapping: general mapping payload
        :return:
        """
        general_settings = WorkspaceGeneralSettings.objects.get(workspace_id=self.__workspace_id)

        if general_settings.corporate_credit_card_expenses_object and \
            general_settings.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
            assert_valid('default_charge_card_name' in general_mapping and general_mapping['default_charge_card_name'],
                         'default charge card name field is blank')
            assert_valid('default_charge_card_id' in general_mapping and general_mapping['default_charge_card_id'],
                         'default charge card id field is blank')

        elif general_settings.corporate_credit_card_expenses_object and \
            general_settings.corporate_credit_card_expenses_object == 'BILL':
            assert_valid('default_ccc_vendor_name' in general_mapping and general_mapping['default_ccc_vendor_name'],
                         'default ccc vendor name field is blank')
            assert_valid('default_ccc_vendor_id' in general_mapping and general_mapping['default_ccc_vendor_id'],
                         'default ccc vendor id field is blank')

        general_mapping, _ = GeneralMapping.objects.update_or_create(
            workspace_id=self.__workspace_id,
            defaults={
                'default_location_name': general_mapping.get('default_location_name') \
                    if general_mapping.get('default_location_name') else None,
                'default_location_id': general_mapping.get('default_location_id') \
                    if general_mapping.get('default_location_id') else None,
                'default_department_name': general_mapping.get('default_department_name') \
                    if general_mapping.get('default_department_name') else None,
                'default_department_id': general_mapping.get('default_department_id') \
                    if general_mapping.get('default_department_id') else None,
                'default_project_name': general_mapping.get('default_project_name') \
                    if general_mapping.get('default_project_name') else None,
                'default_project_id': general_mapping.get('default_project_id') \
                    if general_mapping.get('default_project_id') else None,
                'default_charge_card_name': general_mapping.get('default_charge_card_name') \
                    if general_mapping.get('default_charge_card_name') else None,
                'default_charge_card_id': general_mapping.get('default_charge_card_id') \
                    if general_mapping.get('default_charge_card_id') else None,
                'default_ccc_vendor_name': general_mapping.get('default_ccc_vendor_name') \
                    if general_mapping.get('default_ccc_vendor_name') else None,
                'default_ccc_vendor_id': general_mapping.get('default_ccc_vendor_id') \
                    if general_mapping.get('default_ccc_vendor_id') else None
            }
        )

        return general_mapping
