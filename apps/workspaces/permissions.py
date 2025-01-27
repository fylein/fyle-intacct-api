from rest_framework import permissions
from rest_framework.request import Request
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model

from cryptography.fernet import Fernet

from apps.workspaces.models import Workspace

User = get_user_model()


class WorkspacePermissions(permissions.BasePermission):
    """
    Permission check for users <> workspaces
    """
    @staticmethod
    def validate_and_cache(workspace_users: list, user: User, workspace_id: str, cache_users: bool = False) -> bool:
        """
        Validate if user is part of the workspace and cache the users for 2 days
        :param workspace_users: List of users in the workspace
        :param user: User object
        :param workspace_id: Workspace ID
        :param cache_users: Cache the users
        :return: True if user is part of the workspace, False
        """
        if user.id in workspace_users:
            if cache_users:
                cache.set(workspace_id, workspace_users, 172800)
            return True

        return False

    def has_permission(self, request: Request, view: any) -> bool:
        """
        Check if user is part of the workspace
        :param request: Request object
        :param view: View object
        :return: True if user is part of the workspace, False
        """
        workspace_id = str(view.kwargs.get('workspace_id'))
        user = request.user
        workspace_users = cache.get(workspace_id)

        if workspace_users:
            return self.validate_and_cache(workspace_users, user, workspace_id)
        else:
            workspace_users = Workspace.objects.filter(pk=workspace_id).values_list('user', flat=True)
            return self.validate_and_cache(workspace_users, user, workspace_id, True)


class IsAuthenticatedForInternalAPI(permissions.BasePermission):
    """
    Custom auth for internal APIs
    """
    def has_permission(self, request: Request, view: any) -> bool:
        # Client sends a token in the header, which we decrypt and compare with the Client Secret
        cipher_suite = Fernet(settings.ENCRYPTION_KEY)
        try:
            decrypted_password = cipher_suite.decrypt(request.headers['X-Internal-API-Client-ID'].encode('utf-8')).decode('utf-8')
            if decrypted_password == settings.E2E_TESTS_CLIENT_SECRET:
                return True
        except Exception:
            return False

        return False
