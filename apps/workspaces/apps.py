from django.apps import AppConfig


class WorkspaceConfig(AppConfig):
    """
    Configuration class for the workspaces app.
    """
    name = 'apps.workspaces'

    def ready(self) -> None:
        super(WorkspaceConfig, self).ready()
        import apps.workspaces.signals # noqa
