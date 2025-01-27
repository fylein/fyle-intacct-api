from django.urls import path

from apps.tasks.views import (
    TasksView,
    NewTaskView,
    TasksByIdView,
    TasksByExpenseGroupIdView
)


urlpatterns = [
    path('', TasksByIdView.as_view()),
    path('expense_group/<int:expense_group_id>/', TasksByExpenseGroupIdView.as_view()),
    path('all/', TasksView.as_view()),
    path('v2/all/', NewTaskView.as_view())
]
