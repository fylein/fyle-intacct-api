from django.urls import path

from .export_settings.views import ExportSettingsView
from .import_settings.views import ImportSettingsView
from .advanced_settings.views import AdvancedConfigurationsView
from .errors.views import ErrorsView


urlpatterns = [
    path('<int:workspace_id>/export_settings/', ExportSettingsView.as_view()),
    path('<int:workspace_id>/import_settings/', ImportSettingsView.as_view()),
    path('<int:workspace_id>/advanced_settings/', AdvancedConfigurationsView.as_view()),
    path('<int:workspace_id>/errors/', ErrorsView.as_view()),
]
