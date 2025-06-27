from django.urls import path

from apps.internal.views import AccountingFieldsView, ExportedEntryView, E2ESetupView, E2EDestroyView

urlpatterns = [
    path('accounting_fields/', AccountingFieldsView.as_view(), name='accounting-fields'),
    path('exported_entry/', ExportedEntryView.as_view(), name='exported-entry'),
    path('e2e/setup_org/', E2ESetupView.as_view(), name='e2e-setup-org'),
    path('e2e/destroy/', E2EDestroyView.as_view(), name='e2e-destroy'),
]
