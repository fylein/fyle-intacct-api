from django.apps import AppConfig


class MappingsConfig(AppConfig):
    """
    This class is used to configure the mappings app.
    """
    name = 'apps.mappings'

    def ready(self) -> None:
        super(MappingsConfig, self).ready()
        import apps.mappings.signals # noqa
