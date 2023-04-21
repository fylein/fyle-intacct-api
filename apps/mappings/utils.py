from typing import Dict

from apps.sage_intacct.tasks import schedule_ap_payment_creation, schedule_sage_intacct_reimbursement_creation
from apps.workspaces.models import Configuration
from fyle_intacct_api.utils import assert_valid
from fyle_accounting_mappings.models import MappingSetting

from .models import GeneralMapping
from .tasks import schedule_auto_map_charge_card_employees


class MappingUtils:
    def __init__(self, workspace_id):
        self.__workspace_id = workspace_id

    def create_or_update_general_mapping(self, general_mapping: Dict):
        """
        Create or update general mapping
        :param general_mapping: general mapping payload
        :return:
        """
        configuration = Configuration.objects.get(workspace_id=self.__workspace_id)

        project_setting: MappingSetting = MappingSetting.objects.filter(
            workspace_id=self.__workspace_id,
            destination_field='PROJECT'
        ).first()

        if configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
            assert_valid('default_charge_card_name' in general_mapping and general_mapping['default_charge_card_name'],
                         'default charge card name field is blank')
            assert_valid('default_charge_card_id' in general_mapping and general_mapping['default_charge_card_id'],
                         'default charge card id field is blank')

        elif configuration.corporate_credit_card_expenses_object == 'JOURNAL_ENTRY':
            assert_valid('default_credit_card_name' in general_mapping and general_mapping['default_credit_card_name'],
                         'default credit card name field is blank')
            assert_valid('default_credit_card_id' in general_mapping and general_mapping['default_credit_card_id'],
                         'default credit card id field is blank')

        elif configuration.corporate_credit_card_expenses_object == 'BILL':
            assert_valid('default_ccc_vendor_name' in general_mapping and general_mapping['default_ccc_vendor_name'],
                         'default ccc vendor name field is blank')
            assert_valid('default_ccc_vendor_id' in general_mapping and general_mapping['default_ccc_vendor_id'],
                         'default ccc vendor id field is blank')

        elif configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
            assert_valid('default_ccc_expense_payment_type_name' in general_mapping and
                         general_mapping['default_ccc_expense_payment_type_name'],
                         'default ccc expense payment type name is blank')
            assert_valid('default_ccc_expense_payment_type_id' in general_mapping and
                         general_mapping['default_ccc_expense_payment_type_id'],
                         'default ccc expense payment type id is blank')

        if configuration.sync_fyle_to_sage_intacct_payments:
            assert_valid('payment_account_name' in general_mapping and general_mapping['payment_account_name'],
                         'payment account name field is blank')
            assert_valid('payment_account_id' in general_mapping and general_mapping['payment_account_id'],
                         'payment account id field is blank')
        
        if configuration.import_tax_codes:
            assert_valid('default_tax_code_id' in general_mapping and general_mapping['default_tax_code_id'],
                        'default tax code id is blank')
            assert_valid('default_tax_code_name' in general_mapping and general_mapping['default_tax_code_name'],
                        'default tax code name is blank')

        general_mapping_object, _ = GeneralMapping.objects.update_or_create(
            workspace_id=self.__workspace_id,
            defaults={
                'location_entity_name': general_mapping['location_entity_name'],
                'location_entity_id': general_mapping['location_entity_id'],
                'default_location_name': general_mapping['default_location_name'],
                'default_location_id': general_mapping['default_location_id'],
                'payment_account_name': general_mapping['payment_account_name'],
                'payment_account_id': general_mapping['payment_account_id'],
                'default_department_name': general_mapping['default_department_name'],
                'default_department_id': general_mapping['default_department_id'],
                'default_class_name': general_mapping['default_class_name'],
                'default_class_id': general_mapping['default_class_id'],
                'default_project_name': general_mapping['default_project_name'],
                'default_project_id': general_mapping['default_project_id'],
                'default_charge_card_name': general_mapping['default_charge_card_name'],
                'default_charge_card_id': general_mapping['default_charge_card_id'],
                'default_credit_card_name': general_mapping['default_credit_card_name'],
                'default_credit_card_id': general_mapping['default_credit_card_id'],
                'default_gl_account_name': general_mapping['default_gl_account_name'],
                'default_gl_account_id': general_mapping['default_gl_account_id'],
                'default_ccc_vendor_name': general_mapping['default_ccc_vendor_name'],
                'default_ccc_vendor_id': general_mapping['default_ccc_vendor_id'],
                'default_item_name': general_mapping['default_item_name'],
                'default_item_id': general_mapping['default_item_id'],
                'default_tax_code_id': general_mapping['default_tax_code_id'],
                'default_tax_code_name': general_mapping['default_tax_code_name'],
                'default_reimbursable_expense_payment_type_name': \
                    general_mapping['default_reimbursable_expense_payment_type_name'],
                'default_reimbursable_expense_payment_type_id': \
                    general_mapping['default_reimbursable_expense_payment_type_id'],
                'default_ccc_expense_payment_type_name': general_mapping['default_ccc_expense_payment_type_name'],
                'default_ccc_expense_payment_type_id': general_mapping['default_ccc_expense_payment_type_id'],
                'use_intacct_employee_departments': general_mapping['use_intacct_employee_departments'],
                'use_intacct_employee_locations': general_mapping['use_intacct_employee_locations']
            }
        )

        if configuration.reimbursable_expenses_object == 'BILL':
            schedule_ap_payment_creation(
                sync_fyle_to_sage_intacct_payments=configuration.sync_fyle_to_sage_intacct_payments,
                workspace_id=self.__workspace_id
            )

        if configuration.reimbursable_expenses_object == 'EXPENSE_REPORT':
            schedule_sage_intacct_reimbursement_creation(
                sync_fyle_to_sage_intacct_payments=configuration.sync_fyle_to_sage_intacct_payments,
                workspace_id=self.__workspace_id
            )

        if general_mapping_object.default_charge_card_name:
            schedule_auto_map_charge_card_employees(self.__workspace_id)

        return general_mapping_object
