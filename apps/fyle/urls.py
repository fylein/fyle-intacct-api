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

from .views import (
    CustomFieldView, ExpenseFilterView, ExpenseGroupExpenseView, ExpenseGroupView, ExpenseGroupScheduleView, ExpenseGroupByIdView,
    ExpenseView, EmployeeView, CategoryView, ProjectView, CostCenterView, FyleFieldsView, ExpenseAttributesView,
    ExpenseGroupSettingsView, RefreshFyleDimensionView, SyncFyleDimensionView, ExpenseGroupCountView, DependentFieldView
)

expense_groups_paths = [
    path('expense_groups/', ExpenseGroupView.as_view()),
    path('expense_groups/count/', ExpenseGroupCountView.as_view()),
    path('expense_groups/trigger/', ExpenseGroupScheduleView.as_view()),
    path('expense_groups/<int:pk>/', ExpenseGroupByIdView.as_view()),
    path('expense_groups/<int:expense_group_id>/expenses/', ExpenseGroupExpenseView.as_view()),
    path('employees/', EmployeeView.as_view()),
    path('categories/', CategoryView.as_view()),
    path('projects/', ProjectView.as_view()),
    path('cost_centers/', CostCenterView.as_view()),
    path('expense_group_settings/', ExpenseGroupSettingsView.as_view())
]

fyle_dimension_paths = [
    path('sync_dimensions/', SyncFyleDimensionView.as_view()),
    path('refresh_dimensions/', RefreshFyleDimensionView.as_view())
]

other_paths = [
    path('expense_attributes/', ExpenseAttributesView.as_view()),
    path('fyle_fields/', FyleFieldsView.as_view()),
    path('expense_filters/', ExpenseFilterView.as_view(), name='expense-filters'),
    path('expenses/', ExpenseView.as_view(), name='expenses'),
    path('custom_fields/', CustomFieldView.as_view(), name='custom-field'),
    path('dependent_fields/', DependentFieldView.as_view(), name='dependent-field')
]

urlpatterns = list(itertools.chain(expense_groups_paths, fyle_dimension_paths, other_paths))
