"""
Workspace Serializers
"""
from rest_framework import serializers

from .models import Workspace, Configuration, FyleCredential, SageIntacctCredential, WorkspaceSchedule


class WorkspaceSerializer(serializers.ModelSerializer):
    """
    Workspace serializer
    """
    class Meta:
        model = Workspace
        fields = '__all__'


class ConfigurationSerializer(serializers.ModelSerializer):
    """
    General settings serializer
    """
    workspace = serializers.CharField()

    def create(self, validated_data):
        """
        Create Workspace General Settings
        :param validated_data: Validated data
        :return: upserted general settings object
        """
        workspace = validated_data['workspace']

        configuration, _ = Configuration.objects.update_or_create(
            workspace_id=workspace,
            defaults={
                'reimbursable_expenses_object': validated_data['reimbursable_expenses_object'],
                'corporate_credit_card_expenses_object': validated_data['corporate_credit_card_expenses_object'],
                'sync_fyle_to_sage_intacct_payments': validated_data['sync_fyle_to_sage_intacct_payments'],
                'sync_sage_intacct_to_fyle_payments': validated_data['sync_sage_intacct_to_fyle_payments'],
                'import_projects': validated_data['import_projects'],
                'import_categories': validated_data['import_categories'],
                'auto_map_employees': validated_data['auto_map_employees'],
                'auto_create_destination_entity': validated_data['auto_create_destination_entity']
            }
        )

        return configuration

    def validate(self, data):
        """
        Validate auto create destination entity
        :param data: Non-validated data
        :return: upserted general settings object
        """
        if not data['auto_map_employees'] and data['auto_create_destination_entity']:
            raise serializers.ValidationError(
                'Cannot set auto_create_destination_entity value if auto map employees is disabled')

        if data['auto_map_employees'] == 'EMPLOYEE_CODE' and data['auto_create_destination_entity']:
            raise serializers.ValidationError('Cannot enable auto create destination entity for employee code')

        return data

    class Meta:
        model = Configuration
        fields = '__all__'


class FyleCredentialSerializer(serializers.ModelSerializer):
    """
    Fyle credential serializer
    """
    class Meta:
        model = FyleCredential
        fields = '__all__'


class SageIntacctCredentialSerializer(serializers.ModelSerializer):
    """
    Sage Intacct credential serializer
    """
    class Meta:
        model = SageIntacctCredential
        fields = ['id', 'si_user_id', 'si_company_id', 'si_company_name', 'created_at', 'updated_at', 'workspace_id']


class WorkspaceScheduleSerializer(serializers.ModelSerializer):
    """
    Workspace Schedule serializer
    """
    class Meta:
        model = WorkspaceSchedule
        fields = '__all__'
