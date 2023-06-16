from rest_framework import serializers

from apps.workspaces.models import Configuration, Workspace, WorkspaceSchedule
from apps.mappings.models import GeneralMapping
from .triggers import AdvancedConfigurationsTriggers


class ReadWriteSerializerMethodField(serializers.SerializerMethodField):
    """
    Serializer Method Field to Read and Write from values
    Inherits serializers.SerializerMethodField
    """

    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs['source'] = '*'
        super(serializers.SerializerMethodField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        return {self.field_name: data}


class ConfigurationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Configuration
        fields = [
            'change_accounting_period',
            'sync_fyle_to_sage_intacct_payments',
            'sync_sage_intacct_to_fyle_payments',
            'auto_create_destination_entity',
            'memo_structure'
        ]


class GeneralMappingsSerializer(serializers.ModelSerializer):

    default_location = ReadWriteSerializerMethodField()
    payment_account = ReadWriteSerializerMethodField()
    default_department = ReadWriteSerializerMethodField()
    default_class = ReadWriteSerializerMethodField()
    default_project = ReadWriteSerializerMethodField()
    default_item = ReadWriteSerializerMethodField()
    default_class = ReadWriteSerializerMethodField()

    class Meta:
        model = GeneralMapping
        fields = [
            'default_location',
            'payment_account',
            'default_department',
            'default_class',
            'default_project',
            'default_item',
            'use_intacct_employee_departments',
            'use_intacct_employee_locations'
        ]


    def get_default_location(self, instance):
        return {
            'name': instance.default_location_name,
            'id': instance.default_location_id
        }

    def get_payment_account(self, instance):
        return {
            'name': instance.payment_account_name,
            'id': instance.payment_account_id
        }

    def get_default_department(self, instance):
        return {
            'name': instance.default_department_name,
            'id': instance.default_department_id
        }

    def get_default_class(self, instance):
        return {
            'name': instance.default_class_name,
            'id': instance.default_class_id
        }

    def get_default_project(self, instance):
        return {
            'name': instance.default_project_name,
            'id': instance.default_project_id
        }

    def get_default_item(self, instance):
        return {
            'name': instance.default_item_name,
            'id': instance.default_item_id
        }


class WorkspaceSchedulesSerializer(serializers.ModelSerializer):
    emails_selected = serializers.ListField(allow_null=True, required=False)

    class Meta:
        model = WorkspaceSchedule
        fields = [
            'enabled',
            'interval_hours',
            'additional_email_options',
            'emails_selected'
        ]


class AdvancedConfigurationsSerializer(serializers.ModelSerializer):
    """
    Serializer for the Advanced Configurations Form/API
    """
    configurations = ConfigurationSerializer()
    general_mappings = GeneralMappingsSerializer()
    workspace_schedules = WorkspaceSchedulesSerializer()
    workspace_id = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            'configurations',
            'general_mappings',
            'workspace_schedules',
            'workspace_id'
        ]
        read_only_fields = ['workspace_id']


    def get_workspace_id(self, instance):
        return instance.id


    def update(self, instance, validated):
        configurations = validated.pop('configurations')
        general_mappings = validated.pop('general_mappings')
        workspace_schedules = validated.pop('workspace_schedules')

        configurations_instance, _ = Configuration.objects.update_or_create(
            workspace=instance,
            defaults={
                'sync_fyle_to_sage_intacct_payments': configurations.get('sync_fyle_to_sage_intacct_payments'),
                'sync_sage_intacct_to_fyle_payments': configurations.get('sync_sage_intacct_to_fyle_payments'),
                'auto_create_destination_entity': configurations.get('auto_create_destination_entity'),
                'change_accounting_period': configurations.get('change_accounting_period'),
                'memo_structure': configurations.get('memo_structure')
            }
        )

        GeneralMapping.objects.update_or_create(
            workspace=instance,
            defaults={
                'payment_account_name': general_mappings.get('payment_account').get('name'),
                'payment_account_id': general_mappings.get('payment_account').get('id')
            }
        )


        AdvancedConfigurationsTriggers.run_post_configurations_triggers(instance.id, workspace_schedules)

        if instance.onboarding_state == 'ADVANCED_CONFIGURATION':
            instance.onboarding_state = 'COMPLETE'
            instance.save()

        return instance

    def validate(self, data):
        if not data.get('configurations'):
            raise serializers.ValidationError('Workspace general settings are required')

        if not data.get('general_mappings'):
            raise serializers.ValidationError('General mappings are required')

        if not data.get('workspace_schedules'):
            raise serializers.ValidationError('Workspace Schedules are required')

        return data
