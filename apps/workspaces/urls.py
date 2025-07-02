from django.urls import path, include

from apps.workspaces.views import (
    ReadyView,
    WorkspaceView,
    ConnectFyleView,
    ConfigurationsView,
    ExportToIntacctView,
    WorkspaceAdminsView,
    LastExportDetailView,
    ConnectSageIntacctView,
    TokenHealthView
)

workspace_app_paths = [
    path('', WorkspaceView.as_view({'get': 'get', 'post': 'post'})),
    path('<int:workspace_id>/', WorkspaceView.as_view({'get': 'get_by_id'})),
    path('<int:workspace_id>/configuration/', ConfigurationsView.as_view()),
    path('ready/', ReadyView.as_view({'get': 'get'})),
    path('<int:workspace_id>/exports/trigger/', ExportToIntacctView.as_view({'post': 'post'}), name='export-to-intacct'),
    path('<int:workspace_id>/admins/', WorkspaceAdminsView.as_view({'get': 'get'}), name='admin'),
    path('<int:workspace_id>/export_detail/', LastExportDetailView.as_view(), name='export-detail')
]

fyle_connection_api_paths = [
    path('<int:workspace_id>/connect_fyle/authorization_code/', ConnectFyleView.as_view({'post': 'post'})),
    path('<int:workspace_id>/credentials/fyle/', ConnectFyleView.as_view({'get': 'get'})),
    path('<int:workspace_id>/credentials/fyle/delete/', ConnectFyleView.as_view({'post': 'delete'}))
]

sage_intacct_connection_api_paths = [
    path('<int:workspace_id>/credentials/sage_intacct/delete/', ConnectSageIntacctView.as_view({'post': 'delete'})),
    path('<int:workspace_id>/credentials/sage_intacct/', ConnectSageIntacctView.as_view(
        {'post': 'post', 'get': 'get'})),
    path('<int:workspace_id>/token_health/', TokenHealthView.as_view({'get': 'get'})),
]

other_app_paths = [
    path('<int:workspace_id>/fyle/', include('apps.fyle.urls')),
    path('<int:workspace_id>/sage_intacct/', include('apps.sage_intacct.urls')),
    path('<int:workspace_id>/mappings/', include('apps.mappings.urls')),
    path('<int:workspace_id>/tasks/', include('apps.tasks.urls')),
]

common_resources_paths = [
    path('<int:workspace_id>/common_resources/', include('fyle_accounting_library.common_resources.urls'))
]

urlpatterns = []
urlpatterns.extend(workspace_app_paths)
urlpatterns.extend(fyle_connection_api_paths)
urlpatterns.extend(sage_intacct_connection_api_paths)
urlpatterns.extend(other_app_paths)
urlpatterns.extend(common_resources_paths)
