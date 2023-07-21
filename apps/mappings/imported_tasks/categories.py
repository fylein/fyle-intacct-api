from .base import Base
from datetime import datetime

class Categories(Base):
    """Class for Categories APIs."""

    def __init__(self, workspace_id: int, destination_field: str):
        super().__init__(workspace_id, 'CATEGORY' , destination_field)

    def trigger_import(self):
        self.check_status_and_trigger_import()
