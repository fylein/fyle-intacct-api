import logging

from django.db.models import Q
from django.db import transaction
from django_q.tasks import async_task
from rest_framework import serializers
from fyle_accounting_mappings.models import MappingSetting

from fyle_integrations_imports.models import ImportLog
from apps.mappings.models import GeneralMapping
from apps.fyle.models import DependentFieldSetting
from apps.workspaces.models import Workspace, Configuration
from apps.workspaces.apis.import_settings.triggers import ImportSettingsTrigger

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class MappingSettingFilteredListSerializer(serializers.ListSerializer):
    """
    Serializer to filter the active system, which is a boolen field in
    System Model. The value argument to to_representation() method is
    the model instance
    """
    def to_representation(self, data: list) -> list:
        """
        Filters the active system
        """
        data = data.filter(~Q(
            destination_field__in=[
                'ACCOUNT',
                'CCC_ACCOUNT',
                'CHARGE_CARD_NUMBER',
                'EMPLOYEE',
                'EXPENSE_TYPE',
                'TAX_DETAIL',
                'VENDOR'
            ])
        )
        return super(MappingSettingFilteredListSerializer, self).to_representation(data)


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
        Converts the data to internal value
        """
        return {
            self.field_name: data
        }


class MappingSettingSerializer(serializers.ModelSerializer):
    """
    Mapping Setting Serializer
    """
    class Meta:
        model = MappingSetting
        list_serializer_class = MappingSettingFilteredListSerializer
        fields = [
            'source_field',
            'destination_field',
            'import_to_fyle',
            'is_custom',
            'source_placeholder'
        ]


class ConfigurationsSerializer(serializers.ModelSerializer):
    """
    Configuration Serializer
    """
    class Meta:
        model = Configuration
        fields = [
            'import_categories',
            'import_tax_codes',
            'import_vendors_as_merchants',
            'import_code_fields'
        ]


class GeneralMappingsSerializer(serializers.ModelSerializer):
    """
    General Mappings Serializer
    """
    default_tax_code = ReadWriteSerializerMethodField()

    class Meta:
        model = GeneralMapping
        fields = [
            'default_tax_code'
        ]

    def get_default_tax_code(self, instance: GeneralMapping) -> dict:
        """
        Get default tax code
        """
        return {
            'name': instance.default_tax_code_name,
            'id': instance.default_tax_code_id
        }


class DependentFieldSettingSerializer(serializers.ModelSerializer):
    """
    Dependent Field serializer
    """
    class Meta:
        model = DependentFieldSetting
        fields = [
            'cost_code_field_name',
            'cost_code_placeholder',
            'cost_type_field_name',
            'cost_type_placeholder',
            'is_import_enabled',
            'is_cost_type_import_enabled',
        ]

        read_only_fields = [
            'is_cost_type_import_enabled',
        ]


class ImportSettingsSerializer(serializers.ModelSerializer):
    """
    Import Settings Serializer
    """
    configurations = ConfigurationsSerializer()
    general_mappings = GeneralMappingsSerializer()
    dependent_field_settings = DependentFieldSettingSerializer(allow_null=True, required=False)
    mapping_settings = MappingSettingSerializer(many=True)
    workspace_id = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            'configurations',
            'general_mappings',
            'mapping_settings',
            'dependent_field_settings',
            'workspace_id'
        ]
        read_only_fields = ['workspace_id']

    def get_workspace_id(self, instance: Workspace) -> int:
        """
        Get workspace id
        """
        return instance.id

    def update(self, instance: Configuration, validated: dict) -> Configuration:
        """
        Update the instance
        """
        request = self.context.get('request')
        user = request.user if request and hasattr(request, 'user') else None

        configurations = validated.pop('configurations')
        general_mappings = validated.pop('general_mappings')
        mapping_settings = validated.pop('mapping_settings')
        dependent_field_settings = validated.pop('dependent_field_settings')

        with transaction.atomic():
            configurations_instance, _ = Configuration.objects.update_or_create(
                workspace=instance,
                defaults={
                    'import_categories': configurations.get('import_categories'),
                    'import_tax_codes': configurations.get('import_tax_codes'),
                    'import_vendors_as_merchants': configurations.get('import_vendors_as_merchants'),
                    'import_code_fields': configurations.get('import_code_fields')
                },
                user=user
            )

            GeneralMapping.objects.update_or_create(
                workspace=instance,
                defaults={
                    'default_tax_code_name': general_mappings.get('default_tax_code').get('name'),
                    'default_tax_code_id': general_mappings.get('default_tax_code').get('id')
                },
                user=user
            )

            trigger: ImportSettingsTrigger = ImportSettingsTrigger(
                mapping_settings=mapping_settings,
                workspace_id=instance.id
            )

            trigger.pre_save_mapping_settings()

            if configurations['import_tax_codes']:
                mapping_settings.append({
                    'source_field': 'TAX_GROUP',
                    'destination_field': 'TAX_DETAIL',
                    'import_to_fyle': True,
                    'is_custom': False
                })

            for setting in mapping_settings:
                MappingSetting.objects.update_or_create(
                    destination_field=setting['destination_field'],
                    workspace_id=instance.id,
                    defaults={
                        'source_field': setting['source_field'],
                        'import_to_fyle': setting['import_to_fyle'] if 'import_to_fyle' in setting else False,
                        'is_custom': setting['is_custom'] if 'is_custom' in setting else False,
                        'source_placeholder': setting['source_placeholder'] if 'source_placeholder' in setting else None
                    },
                    user=user
                )

            project_mapping = MappingSetting.objects.filter(workspace_id=instance.id, destination_field='PROJECT').first()
            if project_mapping and project_mapping.import_to_fyle and dependent_field_settings:
                dependent_field_settings['is_cost_type_import_enabled'] = dependent_field_settings.get('cost_type_field_name') is not None

                dependent_field_settings_instance = DependentFieldSetting.objects.filter(workspace_id=instance.id).first()

                reset_flag = False

                if dependent_field_settings_instance:
                    if (
                        (not dependent_field_settings_instance.is_cost_type_import_enabled and not dependent_field_settings.get('cost_type_field_name'))
                        or (dependent_field_settings_instance.is_cost_type_import_enabled and dependent_field_settings.get('cost_type_field_name'))
                    ):
                        reset_flag = False
                    else:
                        reset_flag = True

                if dependent_field_settings_instance and (
                    (dependent_field_settings_instance.cost_type_field_name is not None) != (dependent_field_settings.get('cost_type_field_name') is not None)
                ):
                    dependent_field_settings['last_synced_at'] = None
                    dependent_field_settings['last_successful_import_at'] = None
                    dependent_field_settings['cost_type_field_id'] = dependent_field_settings_instance.cost_type_field_id
                    dependent_field_settings['cost_code_field_id'] = dependent_field_settings_instance.cost_code_field_id
                    if dependent_field_settings_instance.cost_type_field_name is not None:
                        dependent_field_settings['cost_type_field_name'] = dependent_field_settings_instance.cost_type_field_name
                        dependent_field_settings['cost_type_placeholder'] = dependent_field_settings_instance.cost_type_placeholder

                DependentFieldSetting.objects.update_or_create(
                    workspace_id=instance.id,
                    defaults=dependent_field_settings
                )

                if reset_flag:
                    async_task('apps.sage_intacct.dependent_fields.reset_flag_and_disable_cost_type_field', workspace_id=instance.id, reset_flag=reset_flag)

            trigger.post_save_mapping_settings(configurations_instance)

        if instance.onboarding_state == 'IMPORT_SETTINGS':
            instance.onboarding_state = 'ADVANCED_CONFIGURATION'
            instance.save()

        return instance

    def validate(self, data: dict) -> dict:
        """
        Validate the data
        """
        if not data.get('configurations'):
            raise serializers.ValidationError('Workspace general settings are required')

        if data.get('mapping_settings') is None:
            raise serializers.ValidationError('Mapping settings are required')

        if not data.get('general_mappings'):
            raise serializers.ValidationError('General mappings are required')

        if not data.get('dependent_field_settings'):
            pass

        workspace_id = self.context['request'].parser_context.get('kwargs').get('workspace_id')
        import_settings = Configuration.objects.filter(workspace_id=workspace_id).first()
        import_logs = ImportLog.objects.filter(workspace_id=workspace_id).values_list('attribute_type', flat=True)

        is_errored = False
        old_code_pref_list = set()

        if import_settings:
            old_code_pref_list = set(import_settings.import_code_fields)

        new_code_pref_list = set(data.get('configurations', {}).get('import_code_fields', []))
        diff_code_pref_list = list(old_code_pref_list.symmetric_difference(new_code_pref_list))

        logger.info("Import Settings import_code_fields | Content: {{WORKSPACE_ID: {}, Old Import Code Fields: {}, New Import Code Fields: {}}}".format(workspace_id, old_code_pref_list if old_code_pref_list else {}, new_code_pref_list if new_code_pref_list else {}))

        """ If the PROJECT is in the code_fields then we also add Dep fields"""
        mapping_settings = data.get('mapping_settings', [])

        for setting in mapping_settings:
            if setting['destination_field'] == 'PROJECT' and 'PROJECT' in new_code_pref_list:
                if setting['source_field'] == 'PROJECT':
                    new_code_pref_list.update(['COST_CODE', 'COST_TYPE'])
                else:
                    old_code_pref_list.difference_update(['COST_CODE', 'COST_TYPE'])

            if setting['destination_field'] in diff_code_pref_list and setting['source_field'] in import_logs:
                is_errored = True
                break

        # Changes related to ACCOUNT and EXPENSE_TYPE imported as CATEGORY
        # If the ACCOUNT is imported without code we add _ACCOUNT to the code fields
        # same with EXPENSE_TYPE, we add _EXPENSE_TYPE to the code fields
        destination_field = 'ACCOUNT'
        if import_settings.corporate_credit_card_expenses_object == 'EXPENSE_REPORT' \
                or import_settings.reimbursable_expenses_object == 'EXPENSE_REPORT':
            destination_field = 'EXPENSE_TYPE'

        if data.get('configurations').get('import_categories') and destination_field not in new_code_pref_list:
            new_code_pref_list.update(['_{0}'.format(destination_field)])

        if (
            (destination_field == 'ACCOUNT' and 'EXPENSE_TYPE' in diff_code_pref_list)
            or (destination_field == 'EXPENSE_TYPE' and 'ACCOUNT' in diff_code_pref_list)
            or ('ACCOUNT' in new_code_pref_list and '_ACCOUNT' in new_code_pref_list)
            or ('EXPENSE_TYPE' in new_code_pref_list and '_EXPENSE_TYPE' in new_code_pref_list)
            or ('_{0}'.format(destination_field) in new_code_pref_list and destination_field in old_code_pref_list)
            or (destination_field in diff_code_pref_list and '_{0}'.format(destination_field) in old_code_pref_list)
        ):
            is_errored = True

        if not old_code_pref_list.issubset(new_code_pref_list):
            is_errored = True

        if is_errored:
            raise serializers.ValidationError('Cannot change the code fields once they are imported')

        data.get('configurations')['import_code_fields'] = list(new_code_pref_list)

        return data
