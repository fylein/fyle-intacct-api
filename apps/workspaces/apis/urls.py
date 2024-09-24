from django.urls import path

from .export_settings.views import ExportSettingsView
from .import_settings.views import ImportSettingsView, ImportCodeFieldView
from .advanced_settings.views import AdvancedConfigurationsView
from .errors.views import ErrorsView


urlpatterns = [
    path('<int:workspace_id>/export_settings/', ExportSettingsView.as_view()),
    path('<int:workspace_id>/import_settings/import_code_fields_config/', ImportCodeFieldView.as_view(), name='import-code-fields-config'),
    path('<int:workspace_id>/import_settings/', ImportSettingsView.as_view()),
    path('<int:workspace_id>/advanced_settings/', AdvancedConfigurationsView.as_view()),
    path('<int:workspace_id>/errors/', ErrorsView.as_view()),
]
