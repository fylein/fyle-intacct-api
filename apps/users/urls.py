from django.urls import path

from apps.users.views import UserProfileView, FyleOrgsView

urlpatterns = [
    path('profile/', UserProfileView.as_view()),
    path('orgs/', FyleOrgsView.as_view())
]
