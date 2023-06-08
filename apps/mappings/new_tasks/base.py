# TODO: remove unused imports at last
import logging
import traceback
from datetime import datetime, timedelta
from dateutil import parser

from typing import List, Dict

from django_q.models import Schedule
from django_q.tasks import Chain
from fyle_integrations_platform_connector import PlatformConnector

from fyle.platform.exceptions import WrongParamsError, InvalidTokenError as FyleInvalidTokenError, InternalServerError

from fyle_accounting_mappings.helpers import EmployeesAutoMappingHelper
from fyle_accounting_mappings.models import Mapping, MappingSetting, ExpenseAttribute, DestinationAttribute, \
    CategoryMapping, ExpenseField

from sageintacctsdk.exceptions import InvalidTokenError, NoPrivilegeError

from apps.mappings.models import GeneralMapping, ImportLog
from apps.sage_intacct.utils import SageIntacctConnector
from apps.workspaces.models import SageIntacctCredential, FyleCredential, Configuration


logger = logging.getLogger(__name__)
logger.level = logging.INFO



class Base:
    def __init__(self, workspace_id: int, source_field: str, destination_field: str):
        self.workspace_id = workspace_id
        self.source_field = source_field
        self.destination_field = destination_field


    # TODO: Handle exceptions
    def sync_sage_intacct_attributes(self, sageintacct_attribute_type: str):
        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=self.workspace_id)
        sage_intacct_connection = SageIntacctConnector(credentials_object=sage_intacct_credentials, workspace_id=self.workspace_id)
        
        sync_methods = {
            'LOCATION': sage_intacct_connection.sync_locations,
            'PROJECT': sage_intacct_connection.sync_projects,
            'DEPARTMENT': sage_intacct_connection.sync_departments,
            'VENDOR': sage_intacct_connection.sync_vendors,
            'TASK': sage_intacct_connection.sync_tasks,
            'COST_TYPE': sage_intacct_connection.sync_cost_types,
        }
        
        sync_method = sync_methods.get(sageintacct_attribute_type, sage_intacct_connection.sync_user_defined_dimensions)
        sync_method()


    def remove_duplicates_attributes(self, si_attributes: List[DestinationAttribute]):
        unique_attributes = []
        attribute_values = []

        for attribute in si_attributes:
            if attribute.value.lower() not in attribute_values:
                unique_attributes.append(attribute)
                attribute_values.append(attribute.value.lower())

        return unique_attributes


    def construct_fyle_projects_payload(paginated_si_attributes, existing_fyle_attributes, is_auto_sync_status_allowed: bool):
        payload = []

        for attribute in paginated_si_attributes:
            project = {
                'name': attribute.value,
                'code': attribute.destination_id,
                'description': 'Sage Intacct Project - {0}, Id - {1}'.format(
                    attribute.value,
                    attribute.destination_id
                ),
                'is_enabled': attribute.active
            }

            if attribute.value.lower() not in existing_fyle_attributes:
                # Create a new project if it does not exist in Fyle
                payload.append(project)
            elif is_auto_sync_status_allowed and attribute.active is False:
                # Disable the existing project in Fyle if auto-sync status is allowed and the project is inactive in Sage Intacct
                project['id'] = existing_fyle_attributes[attribute.value.lower()]['source_id']
                payload.append(project)

        return payload

    def construct_fyle_categories_payload(paginated_si_attributes, existing_fyle_attributes):
        payload = []

        for attribute in paginated_si_attributes:
            category = {
                'name': attribute.value,
                'code': attribute.destination_id,
                'is_enabled': attribute.active
            }
            if attribute.value.lower() not in existing_fyle_attributes:
                # Create a new category if it does not exist in Fyle
                payload.append(category)
            elif attribute.active is False:
                # Disable the existing category in Fyle if auto-sync status is allowed and the account/expense type is inactive in Sage Intacct
                category['id'] = attribute.source_id
                payload.append(category)

        return payload


    def construct_fyle_cost_centers_payload(paginated_si_attributes, existing_fyle_attributes, is_auto_sync_status_allowed: bool):
        payload = []

        for attribute in paginated_si_attributes:
            if attribute.value.lower() not in existing_fyle_attributes:
                # Create a new cost center if it does not exist in Fyle
                payload.append({
                    'name': attribute.value,
                    'is_enabled': True if attribute.active is None else attribute.active,
                    'description': 'Cost Center - {0}, Id - {1}'.format(
                        attribute.value,
                        attribute.destination_id
                    )
                })

        return payload


    def construct_fyle_tax_groups_payload(paginated_si_attributes, existing_fyle_attributes, is_auto_sync_status_allowed: bool):
        payload = []

        for attribute in paginated_si_attributes:
            if attribute.value.lower() not in existing_fyle_attributes:
                # Create a new tax group if it does not exist in Fyle
                payload.append({
                    'name': attribute.value,
                    'is_enabled': True,
                    'percentage': round((attribute.detail['tax_rate']/100), 2)
                })

        return payload


    def construct_fyle_payload(
            self, paginated_si_attributes, is_auto_sync_status_allowed: bool, platform: PlatformConnector):
        payload_constructors = {
            'PROJECT': (self.construct_fyle_projects_payload, platform.projects),
            'CATEGORY': (self.construct_fyle_categories_payload, platform.categories),
            'COST_CENTER': (self.construct_fyle_cost_centers_payload, platform.cost_centers),
            'TAX_GROUP': (self.construct_fyle_tax_groups_payload, platform.tax_groups)
        }

        payload_constructor, resource_class = payload_constructors[self.source_field]

        # Get Existing Fyle Attributes
        paginated_si_values = [attribute.value for attribute in paginated_si_attributes]
        existing_fyle_attributes = self.get_existing_fyle_attributes(paginated_si_values)

        return payload_constructor(paginated_si_attributes, existing_fyle_attributes, is_auto_sync_status_allowed), resource_class


    def get_existing_fyle_attributes(self, paginated_si_values):
        filters = self.construct_attributes_filter(self.source_field, None, paginated_si_values)
        existing_fyle_attributes_names = ExpenseAttribute.objects.filter(**filters).values('value', 'id')

        # Helps in case insensitive matching and disabling them in Fyle if it's inactive in Intacct
        return {attribute['value'].lower(): attribute['source_id'] for attribute in existing_fyle_attributes_names}



    def get_expense_attributes_generator(self, si_attributes_count: int, import_log: ImportLog):
        batch_size = 200
        filters = self.construct_attributes_filter(self.destination_field, import_log)

        for offset in range(0, si_attributes_count, batch_size):
            limit = offset + batch_size
            paginated_si_attributes = DestinationAttribute.objects.filter(**filters).order_by('value', 'id')[offset:limit]

            # Remove duplicate attributes
            paginated_si_attributes = self.remove_duplicates_attributes(paginated_si_attributes)
            is_last_batch = limit >= si_attributes_count

            yield paginated_si_attributes, is_last_batch


    def get_auto_sync_permission(self):
        is_auto_sync_status_allowed = False
        if (self.destination_field == 'PROJECT' and self.source_field == 'PROJECT') or self.source_field == 'CATEGORY':
            is_auto_sync_status_allowed = True

        return is_auto_sync_status_allowed


    def construct_attributes_filter(self, attribute_type: str, import_log: ImportLog, paginated_si_values: list = []):
        filters = {
            'attribute_type': attribute_type,
            'workspace_id': self.workspace_id
        }

        if import_log.last_successful_run_at:
            filters['updated_at__gte'] = import_log.last_successful_run_at

        if paginated_si_values:
            filters['value__in'] = paginated_si_values

        return filters


    def get_si_attributes_count(self):
        filters = self.construct_attributes_filter(self.destination_field, None)
        return DestinationAttribute.objects.filter(**filters).count()


    def update_import_log_post_import(self, is_last_batch: bool, import_log: ImportLog):
        if is_last_batch:
            import_log.last_successful_run_at = datetime.now()
            import_log.status = 'COMPLETE'
            import_log.processed_batches_count = 0
            import_log.queued_batches_count = 0
        else:
            import_log.processed_batches_count += 1
            import_log.queued_batches_count -= 1

        import_log.save()


    def post_to_fyle_and_sync(self, fyle_payload, resource_class, is_last_batch, import_log: ImportLog):
        # Post Payload to Fyle
        resource_updated_at = datetime.now()
        resource_class.post_bulk(fyle_payload)

        # Sync latest imported fields to Fyle, which helps in auto mapping
        # TODO: do incremental sync, send resource_updated_at and get list of fields updated after posted_time
        resource_class.sync(sync_after=resource_updated_at)

        self.update_import_log_post_import(is_last_batch, import_log)


    def construct_payload_and_import_to_fyle(
            self, platform: PlatformConnector, is_auto_sync_status_allowed: bool,
            import_log: ImportLog
        ):
        is_auto_sync_status_allowed = self.get_auto_sync_permission()

        si_attributes_count = DestinationAttribute.objects.filter(attribute_type=self.destination_field, workspace_id=self.workspace_id).count()

        expense_attributes_generator, is_last_batch = self.get_expense_attributes_generator(si_attributes_count, import_log)

        # Do all operations in batches with generator
        for paginated_si_attributes in expense_attributes_generator:
            # Create Payload
            fyle_payload, resource_class = self.construct_fyle_payload(
                paginated_si_attributes, is_auto_sync_status_allowed, platform)

            if fyle_payload:
                import_log.queued_batches_count += 1
                import_log.save()

                self.post_to_fyle_and_sync(fyle_payload, resource_class, is_last_batch, import_log)


    def sync_fyle_attributes(self):
        """
        Sync Fyle Attributes
        """
        # Initialize Fyle Platform Connector
        fyle_credentials = FyleCredential.objects.get(workspace_id=self.workspace_id)
        platform = PlatformConnector(fyle_credentials=fyle_credentials)

        # Sync Fyle Attributes based on source_field
        sync_methods = {
            'PROJECT': platform.projects.sync,
            'COST_CENTER': platform.cost_centers.sync,
            'CATEGORY': platform.categories.sync,
            'TAX_GROUP': platform.tax_groups.sync
        }

        sync_method = sync_methods.get(self.source_field, platform.expense_custom_fields.sync)
        sync_method()

        return platform

    def import_native_field_to_fyle(self, import_log: ImportLog):
        """
        Import Native Field to Fyle and Auto Create Mappings
        Supported Native Fields: PROJECT, CATEGORY, COST_CENTER, TAX_GROUP
        """
        # Sync Fyle Attributes
        platform = self.sync_fyle_attributes()

        # Sync Sage Intacct Attributes
        self.sync_sage_intacct_attributes(self.destination_field)

        # Construct Payload and Import in Batches
        self.construct_payload_and_import_to_fyle(platform, self.destination_field, import_log)

        # TODO: move mapping out of imports check bulk_create_mappings and optimise it
        Mapping.bulk_create_mappings([], self.source_field, self.destination_field, self.workspace_id)


    def check_status_and_trigger_import(self):
        import_log, _ = ImportLog.objects.get_or_create(
            workspace_id=self.workspace_id,
            attribute_type=self.source_field,
            defaults={
                'status': 'IN_PROGRESS'
            }
        )

        # Trigger Import only if the past import not in progress / enqueued
        if import_log.status not in ['IN_PROGRESS', 'ENQUEUED']:
            # Update the required values since we're beginning the import process
            import_log.status = 'IN_PROGRESS'
            import_log.processed_batches_count = 0
            import_log.queued_batches_count = 0
            import_log.save()

            self.import_native_field_to_fyle(import_log)
