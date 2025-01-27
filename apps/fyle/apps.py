from django.apps import AppConfig


class FyleConfig(AppConfig):
    """
    Fyle app config
    """
    name = 'apps.fyle'

    def ready(self) -> None:
        super(FyleConfig, self).ready()
        import apps.fyle.signals # noqa
