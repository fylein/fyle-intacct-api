from rest_framework import serializers
from django.db.models import Q

from fyle_accounting_mappings.models import MappingSetting

from apps.workspaces.models import Configuration


from .models import GeneralMapping


class GeneralMappingSerializer(serializers.ModelSerializer):
    """
    General mappings group serializer
    """
    workspace = serializers.CharField()

    def create(self, validated_data):
        """
        Create or Update General Mappings
        :param validated_data: Validated data
        :return: upserted general mappings object
        """
        print('validated data', validated_data)
        workspace_id = validated_data.pop('workspace')

        general_mapping_object, _ = GeneralMapping.objects.update_or_create(
            workspace_id=workspace_id,
            defaults=validated_data
        )

        return general_mapping_object


    def validate(self, data):
        """
        Validate auto create destination entity
        :param data: Non-validated data
        :return: upserted general settings object
        """
        print('data', data)
        configuration = Configuration.objects.get(workspace_id=data['workspace'])

        project_setting: MappingSetting = MappingSetting.objects.filter(
            workspace_id=data['workspace'],
            destination_field='PROJECT'
        ).first()

        if configuration.corporate_credit_card_expenses_object == 'CHARGE_CARD_TRANSACTION':
            if (not data['default_charge_card_name'] or not data['default_charge_card_id']):
                raise serializers.ValidationError('default charge card is missing')

        elif configuration.corporate_credit_card_expenses_object == 'BILL':
            if (not data['default_ccc_vendor_name'] or not data['default_ccc_vendor_id']):
                raise serializers.ValidationError('default ccc vendor is missing')

        elif configuration.corporate_credit_card_expenses_object == 'EXPENSE_REPORT':
            if (not data['default_ccc_expense_payment_type_name'] or not data['default_ccc_expense_payment_type_id']):
                raise serializers.ValidationError('default cc expense payment type is missing')

        if project_setting:
            if (not data['default_item_name'] or not data['default_item_id']):
                serializers.ValidationError('default item is missing')

        if configuration.sync_fyle_to_sage_intacct_payments:
            if (not data['payment_account_name'] or not data['payment_account_id']):
                serializers.ValidationError('payment account name is missing')

        return data

    class Meta:
        model = GeneralMapping
        fields = '__all__'
