from .base import Base

class TaxGroup(Base):
    def __init__(self, workspace_id: int, destination_field: str):
        super().__init__(workspace_id, 'TAX_GROUP', destination_field)
        self.check_status_and_trigger_import()
