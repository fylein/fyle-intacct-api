from django.urls import path

from apps.users.views import UserProfileView

urlpatterns = [
    path('profile/', UserProfileView.as_view())
]
