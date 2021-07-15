from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from fyle_rest_auth.models import AuthToken
from fyle_rest_auth.utils import AuthUtils

from apps.fyle.utils import FyleConnector

from apps.workspaces.models import FyleCredential, Workspace

auth_utils = AuthUtils()

class UserProfileView(generics.RetrieveAPIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Get User Details
        """
        fyle_credentials = AuthToken.objects.get(user__user_id=request.user)

        fyle_connector = FyleConnector(fyle_credentials.refresh_token)

        employee_profile = fyle_connector.get_employee_profile()

        return Response(
            data=employee_profile,
            status=status.HTTP_200_OK
        )

class CluserDomainView(generics.RetrieveAPIView):
    """
    CluserDomain view
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Get cluster domain from Fyle
        """
        try:
            fyle_credentials = AuthToken.objects.get(user__user_id=request.user)
            fyle_connector = FyleConnector(fyle_credentials.refresh_token)
            cluser_domain = fyle_connector.get_cluster_domain()['cluster_domain']

            fyle_user = auth_utils.get_fyle_user(fyle_credentials.refresh_token)
            org_id = fyle_user['org_id']

            workspace = Workspace.objects.filter(user__user_id=request.user, fyle_org_id=org_id).first()

            workspace.cluster_domain = cluser_domain
            workspace.save()

            return Response(
                data=cluser_domain,
                status=status.HTTP_200_OK
            )
        except FyleCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Invalid / Expired Token'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class FyleOrgsView(generics.ListCreateAPIView):
    """
    FyleOrgs view
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Get cluster domain from Fyle
        """
        try:
            fyle_credentials = AuthToken.objects.get(user__user_id=request.user)
            fyle_connector = FyleConnector(fyle_credentials.refresh_token)
            cluser_domain = fyle_connector.get_cluster_domain()['cluster_domain']
            fyle_orgs = fyle_connector.get_fyle_orgs(cluser_domain=cluser_domain)

            return Response(
                data=fyle_orgs,
                status=status.HTTP_200_OK
            )
        except FyleCredential.DoesNotExist:
            return Response(
                data={
                    'message': 'Invalid / Expired Token'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
