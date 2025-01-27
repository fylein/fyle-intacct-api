from django.urls import path, include

from apps.mappings.views import GeneralMappingView, AutoMapEmployeeView, LocationEntityMappingView

urlpatterns = [
    path('location_entity/', LocationEntityMappingView.as_view(), name='location-entity'),
    path('general/', GeneralMappingView.as_view()),
    path('auto_map_employees/trigger/', AutoMapEmployeeView.as_view()),
    path('', include('fyle_accounting_mappings.urls'))
]
