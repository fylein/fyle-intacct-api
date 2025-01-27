import itertools

from django.urls import path

from apps.fyle.views import (
    CustomFieldView, ExpenseFilterView, ExpenseGroupExpenseView,
    ExpenseGroupView, ExpenseGroupScheduleView, ExpenseGroupByIdView,
    ExpenseView, EmployeeView, CategoryView, ProjectView, CostCenterView,
    FyleFieldsView, ExpenseAttributesView, ExpenseGroupSettingsView,
    RefreshFyleDimensionView, SyncFyleDimensionView, ExpenseGroupCountView,
    DependentFieldSettingView, ExportableExpenseGroupsView, ExpenseGroupSyncView,
    ExportView
)

expense_groups_paths = [
    path('expense_groups/', ExpenseGroupView.as_view()),
    path('exportable_expense_groups/', ExportableExpenseGroupsView.as_view(), name='exportable-expense-groups'),
    path('expense_groups/count/', ExpenseGroupCountView.as_view()),
    path('expense_groups/trigger/', ExpenseGroupScheduleView.as_view()),
    path('expense_groups/sync/', ExpenseGroupSyncView.as_view(), name='sync-expense-groups'),
    path('expense_groups/<int:pk>/', ExpenseGroupByIdView.as_view()),
    path('expense_groups/<int:expense_group_id>/expenses/', ExpenseGroupExpenseView.as_view()),
    path('employees/', EmployeeView.as_view()),
    path('categories/', CategoryView.as_view()),
    path('projects/', ProjectView.as_view()),
    path('cost_centers/', CostCenterView.as_view()),
    path('expense_group_settings/', ExpenseGroupSettingsView.as_view()),
    path('exports/', ExportView.as_view(), name='exports')
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
    path('dependent_field_settings/', DependentFieldSettingView.as_view(), name='dependent-field')
]

urlpatterns = list(itertools.chain(expense_groups_paths, fyle_dimension_paths, other_paths))
