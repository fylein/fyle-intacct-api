from django.apps import AppConfig


class InternalConfig(AppConfig):
    """
    InternalConfig class
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.internal'
