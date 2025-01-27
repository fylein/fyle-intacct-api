from rest_framework import serializers

from apps.workspaces.models import Workspace, Configuration
from apps.mappings.models import GeneralMapping
from apps.fyle.models import ExpenseGroupSettings
from apps.workspaces.apis.export_settings.triggers import ExportSettingsTrigger


class ReadWriteSerializerMethodField(serializers.SerializerMethodField):
    """
    Serializer Method Field to Read and Write from values
    Inherits serializers.SerializerMethodField
    """
    def __init__(self, method_name: any = None, **kwargs):
        self.method_name = method_name
        kwargs['source'] = '*'
        super(serializers.SerializerMethodField, self).__init__(**kwargs)

    def to_internal_value(self, data: dict) -> dict:
        """
        Method to convert the data to internal value
        """
        return {
            self.field_name: data
        }


class ConfigurationSerializer(serializers.ModelSerializer):
    """
    Configuration Serializer
    """
    class Meta:
        model = Configuration
        fields = [
            'reimbursable_expenses_object',
            'corporate_credit_card_expenses_object',
            'auto_map_employees',
            'is_simplify_report_closure_enabled',
            'employee_field_mapping',
            'use_merchant_in_journal_line'
        ]

        read_only_fields = ['is_simplify_report_closure_enabled']


class GeneralMappingsSerializer(serializers.ModelSerializer):
    """
    General Mappings Serializer
    """
    default_gl_account = ReadWriteSerializerMethodField()
    default_credit_card = ReadWriteSerializerMethodField()
    default_charge_card = ReadWriteSerializerMethodField()
    default_reimbursable_expense_payment_type = ReadWriteSerializerMethodField()
    default_ccc_expense_payment_type = ReadWriteSerializerMethodField()
    default_ccc_vendor = ReadWriteSerializerMethodField()

    class Meta:
        model = GeneralMapping
        fields = [
            'default_gl_account',
            'default_credit_card',
            'default_charge_card',
            'default_reimbursable_expense_payment_type',
            'default_ccc_expense_payment_type',
            'default_ccc_vendor'
        ]

    def get_default_gl_account(self, instance: GeneralMapping) -> dict:
        """
        Get Default GL Account
        """
        return {
            'id': instance.default_gl_account_id,
            'name': instance.default_gl_account_name
        }

    def get_default_credit_card(self, instance: GeneralMapping) -> dict:
        """
        Get Default Credit Card
        """
        return {
            'id': instance.default_credit_card_id,
            'name': instance.default_credit_card_name
        }

    def get_default_charge_card(self, instance: GeneralMapping) -> dict:
        """
        Get Default Charge Card
        """
        return {
            'id': instance.default_charge_card_id,
            'name': instance.default_charge_card_name
        }

    def get_default_reimbursable_expense_payment_type(self, instance: GeneralMapping) -> dict:
        """
        Get Default Reimbursable Expense Payment Type
        """
        return {
            'id': instance.default_reimbursable_expense_payment_type_id,
            'name': instance.default_reimbursable_expense_payment_type_name
        }

    def get_default_ccc_expense_payment_type(self, instance: GeneralMapping) -> dict:
        """
        Get Default CCC Expense Payment Type
        """
        return {
            'id': instance.default_ccc_expense_payment_type_id,
            'name': instance.default_ccc_expense_payment_type_name
        }

    def get_default_ccc_vendor(self, instance: GeneralMapping) -> dict:
        """
        Get Default CCC Vendor
        """
        return {
            'id': instance.default_ccc_vendor_id,
            'name': instance.default_ccc_vendor_name
        }


class ExpenseGroupSettingsSerializer(serializers.ModelSerializer):
    """
    Expense Group Settings Serializer
    """
    reimbursable_expense_group_fields = serializers.ListField(allow_null=True, required=False)
    reimbursable_export_date_type = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    expense_state = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    corporate_credit_card_expense_group_fields = serializers.ListField(allow_null=True, required=False)
    ccc_export_date_type = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    ccc_expense_state = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    split_expense_grouping = serializers.CharField(allow_null=False, allow_blank=False, required=True)

    class Meta:
        model = ExpenseGroupSettings
        fields = [
            'reimbursable_expense_group_fields',
            'reimbursable_export_date_type',
            'expense_state',
            'corporate_credit_card_expense_group_fields',
            'ccc_export_date_type',
            'ccc_expense_state',
            'split_expense_grouping'
        ]


class ExportSettingsSerializer(serializers.ModelSerializer):
    """
    Export Settings Serializer
    """
    configurations = ConfigurationSerializer()
    expense_group_settings = ExpenseGroupSettingsSerializer()
    general_mappings = GeneralMappingsSerializer()
    workspace_id = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            'configurations',
            'expense_group_settings',
            'general_mappings',
            'workspace_id'
        ]
        read_only_fields = ['workspace_id']

    def get_workspace_id(self, instance: Workspace) -> int:
        """
        Get Workspace ID
        """
        return instance.id

    def update(self, instance: Configuration, validated: dict) -> Configuration:
        """
        Update Configuration
        """
        request = self.context.get('request')
        user = request.user if request and hasattr(request, 'user') else None

        configurations = validated.pop('configurations')
        expense_group_settings = validated.pop('expense_group_settings')
        general_mappings = validated.pop('general_mappings')
        workspace_id = instance.id

        configuration_instance, _ = Configuration.objects.update_or_create(
            workspace_id=workspace_id,
            defaults={
                'auto_map_employees': configurations['auto_map_employees'],
                'reimbursable_expenses_object': configurations['reimbursable_expenses_object'],
                'corporate_credit_card_expenses_object': configurations['corporate_credit_card_expenses_object'],
                'employee_field_mapping': configurations['employee_field_mapping'],
                'use_merchant_in_journal_line': configurations['use_merchant_in_journal_line'] if 'use_merchant_in_journal_line' in configurations else False
            },
            user=user
        )

        export_trigger = ExportSettingsTrigger(
            workspace_id=workspace_id,
            configuration=configuration_instance
        )

        export_trigger.post_save_configurations()

        if not expense_group_settings['reimbursable_expense_group_fields']:
            expense_group_settings['reimbursable_expense_group_fields'] = ['employee_email', 'report_id', 'fund_source', 'claim_number']

        if not expense_group_settings['corporate_credit_card_expense_group_fields']:
            expense_group_settings['corporate_credit_card_expense_group_fields'] = ['employee_email', 'report_id', 'fund_source', 'claim_number']

        if not expense_group_settings['reimbursable_export_date_type']:
            expense_group_settings['reimbursable_export_date_type'] = 'current_date'

        if not expense_group_settings['ccc_export_date_type']:
            expense_group_settings['ccc_export_date_type'] = 'current_date'

        ExpenseGroupSettings.update_expense_group_settings(expense_group_settings, workspace_id=workspace_id, user=user)

        GeneralMapping.objects.update_or_create(
            workspace=instance,
            defaults={
                'default_gl_account_id': general_mappings['default_gl_account']['id'],
                'default_gl_account_name': general_mappings['default_gl_account']['name'],
                'default_credit_card_id': general_mappings['default_credit_card']['id'],
                'default_credit_card_name': general_mappings['default_credit_card']['name'],
                'default_charge_card_id': general_mappings['default_charge_card']['id'],
                'default_charge_card_name': general_mappings['default_charge_card']['name'],
                'default_reimbursable_expense_payment_type_id': general_mappings['default_reimbursable_expense_payment_type']['id'],
                'default_reimbursable_expense_payment_type_name': general_mappings['default_reimbursable_expense_payment_type']['name'],
                'default_ccc_expense_payment_type_id': general_mappings['default_ccc_expense_payment_type']['id'],
                'default_ccc_expense_payment_type_name': general_mappings['default_ccc_expense_payment_type']['name'],
                'default_ccc_vendor_id': general_mappings['default_ccc_vendor']['id'],
                'default_ccc_vendor_name': general_mappings['default_ccc_vendor']['name']
            },
            user=user
        )

        if instance.onboarding_state == 'EXPORT_SETTINGS':
            instance.onboarding_state = 'IMPORT_SETTINGS'
            instance.save()

        return instance

    def validate(self, data: dict) -> dict:
        """
        Validate Export Settings
        """
        # We dont need to validate confiugurations and general mappings as they validations for individual fields
        if not data.get('expense_group_settings'):
            raise serializers.ValidationError('Expense group settings are required')

        if not data.get('configurations'):
            raise serializers.ValidationError('Configurations settings are required')

        if not data.get('general_mappings'):
            raise serializers.ValidationError('General mappings are required')

        return data
