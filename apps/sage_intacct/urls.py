"""fyle_intacct_api URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
import itertools

from .views import  SageIntacctFieldsView, DestinationAttributesView, SyncSageIntacctDimensionView, \
    RefreshSageIntacctDimensionView, DestinationAttributesCountView, \
    TriggerExportsView, TriggerPaymentsView, PaginatedDestinationAttributesView


sage_intacct_app_path = [
    path('sage_intacct_fields/', SageIntacctFieldsView.as_view()),
    path('destination_attributes/', DestinationAttributesView.as_view()),
    path('paginated_destination_attributes/', PaginatedDestinationAttributesView.as_view()),
    path('destination_attributes/count/', DestinationAttributesCountView.as_view()),
    path('exports/trigger/', TriggerExportsView.as_view()),
    path('payments/trigger/', TriggerPaymentsView.as_view()),
]

sage_intacct_dimension_paths = [
    path('sync_dimensions/', SyncSageIntacctDimensionView.as_view()),
    path('refresh_dimensions/', RefreshSageIntacctDimensionView.as_view()),
]

urlpatterns = list(itertools.chain(sage_intacct_app_path, sage_intacct_dimension_paths))
