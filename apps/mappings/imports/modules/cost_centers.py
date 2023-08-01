from .base import Base
from fyle_accounting_mappings.models import DestinationAttribute

class CostCenter(Base):
    def __init__(self, workspace_id: int, destination_field: str):
        super().__init__(workspace_id, 'COST_CENTER' , destination_field, 'cost_centers')

    def trigger_import(self):
        self.check_import_log_and_start_import()

def trigger_import_via_schedule(workspace_id: int, destination_field: str):
    project = CostCenter(workspace_id, destination_field)
    project.trigger_import()

