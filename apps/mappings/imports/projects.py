from .base import Base
from fyle_accounting_mappings.models import DestinationAttribute

class Project(Base):
    def __init__(self, workspace_id: int, destination_field: str):
        super().__init__(workspace_id, 'PROJECT' , destination_field, 'projects')

    def trigger_import(self):
        self.check_import_log_and_start_import()

    def construct_fyle_payload(
            self,
            paginated_si_attributes,
            existing_fyle_attributes_map,
            is_auto_sync_status_allowed: bool
    ):
        print("""




            Projects payload block is used""")
        
        print(paginated_si_attributes)
        print(existing_fyle_attributes_map)
        print(is_auto_sync_status_allowed)

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
            print(attribute)

            if attribute.value.lower() not in existing_fyle_attributes_map:
                # Create a new project if it does not exist in Fyle
                payload.append(project)
            elif is_auto_sync_status_allowed and not attribute.active:
                print("inside elfi block ")
                # Disable the existing project in Fyle if auto-sync status is allowed and the project is inactive in Sage Intacct
                project['id'] = existing_fyle_attributes_map[attribute.value.lower()]
                payload.append(project)

        return payload


#TODO changhe the imported_task to imports