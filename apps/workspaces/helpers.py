def get_error_model_path() -> str:
    """
    Get error model path: This is for imports submodule
    :return: str
    """
    return 'apps.tasks.models.Error'


def get_import_configuration_model_path() -> str:
    """
    Get import configuration model path: This is for imports submodule
    :return: str
    """
    return 'apps.workspaces.models.Configuration'


def get_cost_code_update_method_path() -> str:
    """
    Update and disable cost code path
    :return: str
    """
    return 'apps.sage_intacct.dependent_fields.update_and_disable_cost_code'


def get_app_name() -> str:
    """
    Get app name
    :return: str
    """
    return 'INTACCT'
