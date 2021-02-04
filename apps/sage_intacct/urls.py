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

from .views import EmployeeView, VendorView, AccountView, ExpenseTypeView, ChargeCardAccountView, DepartmentView, \
    ProjectView, LocationView, ExpenseReportView, ExpenseReportScheduleView, BillView, BillScheduleView, \
    ChargeCardTransactionsView, ChargeCardTransactionsScheduleView, SageIntacctFieldsView, APPaymentView,\
    ReimbursementView, PaymentAccountView

urlpatterns = [
    path('employees/', EmployeeView.as_view()),
    path('vendors/', VendorView.as_view()),
    path('accounts/', AccountView.as_view()),
    path('payment_accounts/', PaymentAccountView.as_view()),
    path('expense_types/', ExpenseTypeView.as_view()),
    path('charge_card_accounts/', ChargeCardAccountView.as_view()),
    path('departments/', DepartmentView.as_view()),
    path('projects/', ProjectView.as_view()),
    path('locations/', LocationView.as_view()),
    path('expense_reports/', ExpenseReportView.as_view()),
    path('expense_reports/trigger/', ExpenseReportScheduleView.as_view()),
    path('bills/', BillView.as_view()),
    path('bills/trigger/', BillScheduleView.as_view()),
    path('charge_card_transactions/', ChargeCardTransactionsView.as_view()),
    path('charge_card_transactions/trigger/', ChargeCardTransactionsScheduleView.as_view()),
    path('sage_intacct_fields/', SageIntacctFieldsView.as_view()),
    path('ap_payments/', APPaymentView.as_view()),
    path('reimbursements/', ReimbursementView.as_view())
]
