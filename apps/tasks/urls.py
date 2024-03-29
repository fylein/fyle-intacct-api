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

from .views import TasksByIdView, TasksByExpenseGroupIdView, TasksView, NewTaskView

urlpatterns = [
    path('', TasksByIdView.as_view()),
    path('expense_group/<int:expense_group_id>/', TasksByExpenseGroupIdView.as_view()),
    path('all/', TasksView.as_view()),
    path('v2/all/', NewTaskView.as_view())
]
