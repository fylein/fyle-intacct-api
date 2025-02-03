from django.urls import path

from apps.workspaces.apis.errors.views import ErrorsView
from apps.workspaces.apis.export_settings.views import ExportSettingsView
from apps.workspaces.apis.advanced_settings.views import AdvancedConfigurationsView
from apps.workspaces.apis.import_settings.views import ImportSettingsView, ImportCodeFieldView


urlpatterns = [
    path('<int:workspace_id>/export_settings/', ExportSettingsView.as_view()),
    path('<int:workspace_id>/import_settings/import_code_fields_config/', ImportCodeFieldView.as_view(), name='import-code-fields-config'),
    path('<int:workspace_id>/import_settings/', ImportSettingsView.as_view()),
    path('<int:workspace_id>/advanced_settings/', AdvancedConfigurationsView.as_view()),
    path('<int:workspace_id>/errors/', ErrorsView.as_view()),
]
