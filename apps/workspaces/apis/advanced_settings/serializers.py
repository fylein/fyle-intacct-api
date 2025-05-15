from rest_framework import serializers
from django_q.tasks import async_task

from apps.mappings.models import GeneralMapping
from apps.workspaces.models import Configuration, Workspace, WorkspaceSchedule
from apps.workspaces.apis.advanced_settings.triggers import AdvancedConfigurationsTriggers


class ReadWriteSerializerMethodField(serializers.SerializerMethodField):
    """
    Serializer Method Field to Read and Write from values
    Inherits serializers.SerializerMethodField
    """
    def __init__(self, method_name: any = None, **kwargs) -> None:
        self.method_name = method_name
        kwargs['source'] = '*'
        super(serializers.SerializerMethodField, self).__init__(**kwargs)

    def to_internal_value(self, data: dict) -> dict:
        """
        Method to convert the data to internal value
        :param data: Data to be converted
        :return: Converted Data
        """
        return {self.field_name: data}


class ConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Configuration Form/API
    """
    class Meta:
        model = Configuration
        fields = [
            'change_accounting_period',
            'sync_fyle_to_sage_intacct_payments',
            'sync_sage_intacct_to_fyle_payments',
            'auto_create_destination_entity',
            'memo_structure',
            'auto_create_merchants_as_vendors',
            'je_single_credit_line'
        ]


class GeneralMappingsSerializer(serializers.ModelSerializer):
    """
    Serializer for the General Mappings Form/API
    """
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

    def get_default_location(self, instance: GeneralMapping) -> dict:
        """
        Method to get default location
        :param instance: General Mapping Instance
        :return: Default Location
        """
        return {
            'name': instance.default_location_name,
            'id': instance.default_location_id
        }

    def get_payment_account(self, instance: GeneralMapping) -> dict:
        """
        Method to get payment account
        :param instance: General Mapping Instance
        :return: Payment Account
        """
        return {
            'name': instance.payment_account_name,
            'id': instance.payment_account_id
        }

    def get_default_department(self, instance: GeneralMapping) -> dict:
        """
        Method to get default department
        :param instance: General Mapping Instance
        :return: Default Department
        """
        return {
            'name': instance.default_department_name,
            'id': instance.default_department_id
        }

    def get_default_class(self, instance: GeneralMapping) -> dict:
        """
        Method to get default class
        :param instance: General Mapping Instance
        :return: Default Class
        """
        return {
            'name': instance.default_class_name,
            'id': instance.default_class_id
        }

    def get_default_project(self, instance: GeneralMapping) -> dict:
        """
        Method to get default project
        :param instance: General Mapping Instance
        :return: Default Project
        """
        return {
            'name': instance.default_project_name,
            'id': instance.default_project_id
        }

    def get_default_item(self, instance: GeneralMapping) -> dict:
        """
        Method to get default item
        :param instance: General Mapping Instance
        :return: Default Item
        """
        return {
            'name': instance.default_item_name,
            'id': instance.default_item_id
        }


class WorkspaceSchedulesSerializer(serializers.ModelSerializer):
    """
    Serializer for the Workspace Schedules Form/API
    """
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

    def get_workspace_id(self, instance: Workspace) -> int:
        """
        Method to get workspace id
        :param instance: Workspace Instance
        :return: Workspace ID
        """
        return instance.id

    def update(self, instance: Configuration, validated: dict) -> Configuration:
        """
        Method to update the instance
        :param instance: Configuration Instance
        :param validated: Validated Data
        :return: Updated Configuration Instance
        """
        request = self.context.get('request')
        user = request.user if request and hasattr(request, 'user') else None

        configurations = validated.pop('configurations')
        general_mappings = validated.pop('general_mappings')
        workspace_schedules = validated.pop('workspace_schedules')

        Configuration.objects.update_or_create(
            workspace=instance,
            defaults={
                'sync_fyle_to_sage_intacct_payments': configurations.get('sync_fyle_to_sage_intacct_payments'),
                'sync_sage_intacct_to_fyle_payments': configurations.get('sync_sage_intacct_to_fyle_payments'),
                'auto_create_destination_entity': configurations.get('auto_create_destination_entity'),
                'change_accounting_period': configurations.get('change_accounting_period'),
                'memo_structure': configurations.get('memo_structure'),
                'auto_create_merchants_as_vendors': configurations.get('auto_create_merchants_as_vendors'),
                'je_single_credit_line': configurations.get('je_single_credit_line')
            },
            user=user
        )

        GeneralMapping.objects.update_or_create(
            workspace=instance,
            defaults={
                'payment_account_name': general_mappings.get('payment_account').get('name'),
                'payment_account_id': general_mappings.get('payment_account').get('id'),
                'default_location_id': general_mappings.get('default_location').get('id'),
                'default_location_name': general_mappings.get('default_location').get('name'),
                'default_department_id': general_mappings.get('default_department').get('id'),
                'default_department_name': general_mappings.get('default_department').get('name'),
                'default_class_id': general_mappings.get('default_class').get('id'),
                'default_class_name': general_mappings.get('default_class').get('name'),
                'default_project_id': general_mappings.get('default_project').get('id'),
                'default_project_name': general_mappings.get('default_project').get('name'),
                'default_item_id': general_mappings.get('default_item').get('id'),
                'default_item_name': general_mappings.get('default_item').get('name'),
                'use_intacct_employee_departments': general_mappings.get('use_intacct_employee_departments'),
                'use_intacct_employee_locations': general_mappings.get('use_intacct_employee_locations')
            },
            user=user
        )

        AdvancedConfigurationsTriggers.run_post_configurations_triggers(instance.id, workspace_schedules)

        if instance.onboarding_state == 'ADVANCED_CONFIGURATION':
            instance.onboarding_state = 'COMPLETE'
            instance.save()

            AdvancedConfigurationsTriggers.post_to_integration_settings(instance.id, True)
            async_task('apps.workspaces.tasks.async_create_admin_subcriptions', instance.id)

        return instance

    def validate(self, data: dict) -> dict:
        """
        Method to validate the data
        :param data: Data to be validated
        :return: Validated Data
        """
        if not data.get('configurations'):
            raise serializers.ValidationError('Workspace general settings are required')

        if not data.get('general_mappings'):
            raise serializers.ValidationError('General mappings are required')

        if not data.get('workspace_schedules'):
            raise serializers.ValidationError('Workspace Schedules are required')

        return data
