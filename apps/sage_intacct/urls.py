import itertools

from django.urls import path

from apps.sage_intacct.views import (
    SageIntacctFieldsView,
    DestinationAttributesView,
    SyncSageIntacctDimensionView,
    RefreshSageIntacctDimensionView,
    PaginatedDestinationAttributesView,
    AuthorizationCodeView
)


sage_intacct_app_path = [
    path('sage_intacct_fields/', SageIntacctFieldsView.as_view()),
    path('destination_attributes/', DestinationAttributesView.as_view()),
    path('paginated_destination_attributes/', PaginatedDestinationAttributesView.as_view()),
    path('credentials/authorization_code/', AuthorizationCodeView.as_view()),
]

sage_intacct_dimension_paths = [
    path('sync_dimensions/', SyncSageIntacctDimensionView.as_view()),
    path('refresh_dimensions/', RefreshSageIntacctDimensionView.as_view()),
]

urlpatterns = list(itertools.chain(sage_intacct_app_path, sage_intacct_dimension_paths))
