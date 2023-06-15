from apps.workspaces.models import Configuration
from apps.sage_intacct.helpers import schedule_payment_sync


class AdvancedConfigurationsTriggers:
    """
    Class containing all triggers for advanced_configurations
    """
    @staticmethod
    def run_configurations_triggers(configurations_instance: Configuration):
        """
        Run workspace general settings triggers
        """
        schedule_payment_sync(configurations_instance)
