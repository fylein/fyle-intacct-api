import math
from typing import List
from datetime import (
    datetime,
    timedelta,
    timezone
)
from fyle_integrations_platform_connector import PlatformConnector
from fyle_accounting_mappings.models import (
    Mapping,
    DestinationAttribute,
    ExpenseAttribute
)

from apps.workspaces.models import FyleCredential
from apps.mappings.models import ImportLog
from apps.workspaces.models import SageIntacctCredential
from apps.sage_intacct.utils import SageIntacctConnector
from apps.mappings.exceptions import handle_exceptions


class Base:
    def __init__(self, workspace_id: int, source_field: str, destination_field: str, class_name: str, sync_after:datetime):
        self.workspace_id = workspace_id
        self.source_field = source_field
        self.destination_field = destination_field
        self.class_name = class_name
        self.sync_after = sync_after


    def __get_platform_class(self, platform: PlatformConnector):

        platform_class = getattr(platform, self.class_name)
        return platform_class
    
    def __get_auto_sync_permission(self):
        is_auto_sync_status_allowed = False
        if (self.destination_field == 'PROJECT' and self.source_field == 'PROJECT') or self.source_field == 'CATEGORY':
            is_auto_sync_status_allowed = True

        return is_auto_sync_status_allowed
    
    def __construct_attributes_filter(self, attribute_type: str, import_log: ImportLog, paginated_si_values: list = []):
        filters = {
            'attribute_type': attribute_type,
            'workspace_id': self.workspace_id
        }

        #TODO : Check if this can cause a problem for category and custom_fields
        if import_log.last_successful_run_at:
            filters['updated_at__gte'] = import_log.last_successful_run_at

        if paginated_si_values:
            filters['value__in'] = paginated_si_values

        return filters
    
    def __remove_duplicate_attributes(self, si_attributes: List[DestinationAttribute]):
        unique_attributes = []
        attribute_values = []

        for attribute in si_attributes:
            if attribute.value.lower() not in attribute_values:
                unique_attributes.append(attribute)
                attribute_values.append(attribute.value.lower())

        return unique_attributes


    def check_import_log_and_start_import(self):
        """
        checks if the import is already in progress and if not, starts the import process
        """
        print("""
              
            check_import_log_and_start_import()
            
        """)
        import_log, is_created = ImportLog.objects.get_or_create(
            workspace_id=self.workspace_id,
            attribute_type=self.source_field,
            defaults={
                'status': 'IN_PROGRESS'
            }
        )
        # and updated_at < now() - interval '30 mins'
        time_diff = datetime.now() - timedelta(minutes=30)
        offset_aware_datetime_diff = time_diff.replace(tzinfo=timezone.utc)
        if import_log.status == 'IN_PROGRESS' and not is_created and import_log.updated_at < (offset_aware_datetime_diff):
            print("In the If block")
            return

        else:
            # Update the required values since we're beginning the import process
            print("In the else block")
            import_log.status = 'IN_PROGRESS'
            import_log.processed_batches_count = 0
            import_log.total_batches_count = 0
            import_log.save()

            self.import_destination_attribute_to_fyle(import_log)

    @handle_exceptions
    def import_destination_attribute_to_fyle(self, import_log: ImportLog):
        """
        Import Native Field to Fyle and Auto Create Mappings
        Supported Native Fields: PROJECT, CATEGORY, COST_CENTER, TAX_GROUP
        """

        # Sync Fyle Attributes
        fyle_credentials = FyleCredential.objects.get(workspace_id=self.workspace_id)
        platform = PlatformConnector(fyle_credentials=fyle_credentials)

        self.sync_expense_attributes(platform)

        # Sync Sage Intacct Attributes
        self.sync_destination_attributes(self.destination_field)

        # Construct Payload and Import in Batches
        self.construct_payload_and_import_to_fyle(platform, self.destination_field, import_log)
        
        self.sync_expense_attributes(platform)

        self.create_mappings()

    def __get_destination_attribute_generator(self):
        # Model query with pagination
        # query only unmapped values
        # yield each page
        batch_size = 200
        destination_attribute_count = DestinationAttribute.objects.filter(attribute_type=self.destination_field, workspace_id=self.workspace_id, mapping__isnull=True).count()

        for offset in range(0, destination_attribute_count, batch_size):
            limit = offset + batch_size
            paginated_destination_attributes = DestinationAttribute.objects.filter(attribute_type=self.destination_field, workspace_id=self.workspace_id, mapping__isnull=True).order_by('value', 'id')[offset:limit]

            # Remove duplicate attributes
            paginated_destination_attributes = self.__remove_duplicate_attributes(paginated_destination_attributes)

            yield paginated_destination_attributes

    def create_mappings(self):
        destination_attributes_generator = self.__get_destination_attribute_generator()
        for paginated_destination_attributes in destination_attributes_generator:
            Mapping.bulk_create_mappings(paginated_destination_attributes, self.source_field, self.destination_field, self.workspace_id)

    def sync_expense_attributes(self, platform: PlatformConnector):
        platform_class = self.__get_platform_class(platform)
        if self.sync_after is not None:
            platform_class.sync(self.sync_after)
        else:
            platform_class.sync()

    
    def sync_destination_attributes(self, sageintacct_attribute_type: str):
        sage_intacct_credentials = SageIntacctCredential.objects.get(workspace_id=self.workspace_id)
        sage_intacct_connection = SageIntacctConnector(credentials_object=sage_intacct_credentials, workspace_id=self.workspace_id)

        print('Syncing Sage Intacct Attributes')
        sync_methods = {
            'LOCATION': sage_intacct_connection.sync_locations,
            'PROJECT': sage_intacct_connection.sync_projects,
            'DEPARTMENT': sage_intacct_connection.sync_departments,
            'VENDOR': sage_intacct_connection.sync_vendors,
            'CLASS': sage_intacct_connection.sync_classes,
            'TAX_DETAIL': sage_intacct_connection.sync_tax_details,
            'ITEM': sage_intacct_connection.sync_items,
            'CUSTOMER': sage_intacct_connection.sync_customers,
            'COST_TYPE': sage_intacct_connection.sync_cost_types,
        }
        
        sync_method = sync_methods.get(sageintacct_attribute_type, sage_intacct_connection.sync_user_defined_dimensions)
        sync_method()


    def construct_payload_and_import_to_fyle(
        self,
        platform: PlatformConnector,
        is_auto_sync_status_allowed: bool,
        import_log: ImportLog
    ):
        """
        Construct Payload and Import to fyle in Batches
        """
        print("""

            construct_payload_and_import_to_fyle()


        """)
        is_auto_sync_status_allowed = self.__get_auto_sync_permission()

        si_attributes_count = DestinationAttribute.objects.filter(attribute_type=self.destination_field, workspace_id=self.workspace_id).count()

        import_log.total_batches_count = math.ceil(si_attributes_count/2)
        import_log.save()

        #this gives the paginated si attributes
        destination_attributes_generator = self.get_destination_attributes_generator(si_attributes_count, import_log)

        # Do all operations in batches with generator
        for paginated_si_attributes, is_last_batch in destination_attributes_generator:
            # Create Payload
            fyle_payload = self.setup_fyle_payload_creation(
                paginated_si_attributes=paginated_si_attributes,
                is_auto_sync_status_allowed=is_auto_sync_status_allowed,
                import_log=import_log
            )
            print("""

                This si the fyle payload

            """)
            print(fyle_payload)
            # Fix this part the update of import_log should be called ragrdless of the fyle payload
            platform_class = self.__get_platform_class(platform)

            self.post_to_fyle_and_sync(
                fyle_payload=fyle_payload,
                resource_class=platform_class,
                is_last_batch=is_last_batch,
                import_log=import_log
            )

    def get_destination_attributes_generator(self, si_attributes_count: int, import_log: ImportLog):
        batch_size = 2
        filters = self.__construct_attributes_filter(self.destination_field, import_log)
        print("""
              
              Thsis si the genrator ka count
              
              
              
              
            """)
        for offset in range(0, si_attributes_count, batch_size):
            limit = offset + batch_size
            print(limit)
            print(si_attributes_count)
            paginated_si_attributes = DestinationAttribute.objects.filter(**filters).order_by('value', 'id')[offset:limit]

            # Remove duplicate attributes
            paginated_si_attributes = self.__remove_duplicate_attributes(paginated_si_attributes)
            is_last_batch = True if limit >= si_attributes_count else False

            print('is_last_batch', is_last_batch)
            print(paginated_si_attributes, 'paginated_si_attributes')
            yield paginated_si_attributes, is_last_batch

    def setup_fyle_payload_creation(
        self,
        paginated_si_attributes: List[DestinationAttribute],
        is_auto_sync_status_allowed: bool,
        import_log: ImportLog
    ):

        # Get Existing Fyle Attributes
        paginated_si_values = [attribute.value for attribute in paginated_si_attributes]
        existing_fyle_attributes_map = self.get_existing_fyle_attributes(paginated_si_values, import_log)

        return self.construct_fyle_payload(paginated_si_attributes, existing_fyle_attributes_map, is_auto_sync_status_allowed)
    
    def get_existing_fyle_attributes(self, paginated_si_values, import_log: ImportLog):
        filters = self.__construct_attributes_filter(self.source_field, import_log, paginated_si_values)
        existing_fyle_attributes_names = ExpenseAttribute.objects.filter(**filters).values('value', 'source_id')

        # Helps in case insensitive matching and disabling them in Fyle if it's inactive in Intacct
        # This is a map of attribute name to attribute source_id
        return {attribute['value'].lower(): attribute['source_id'] for attribute in existing_fyle_attributes_names}
    
    def post_to_fyle_and_sync(self, fyle_payload, resource_class, is_last_batch, import_log: ImportLog):
        # Post Payload to Fyle
        if fyle_payload:
            resource_class.post_bulk(fyle_payload)

        self.update_import_log_post_import(is_last_batch, import_log)

    def update_import_log_post_import(self, is_last_batch: bool, import_log: ImportLog):
        print("""




            update_import_log_post_import()

        """)
        if is_last_batch:
            print("""
                  
                  
                  
                  This isi the if block 
                  
                  
                  """)
            print('is_last_batch', is_last_batch)
            import_log.last_successful_run_at = datetime.now()
            import_log.processed_batches_count += 1
            import_log.status = 'COMPLETE'
            import_log.error_log = []
        else:
            import_log.processed_batches_count += 1
            print("Adding is done")
            print(import_log.processed_batches_count)
            print(import_log.total_batches_count)

        import_log.save()
