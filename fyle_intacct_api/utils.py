from rest_framework.views import Response
from rest_framework.serializers import ValidationError
from apps.workspaces.models import SageIntacctCredential
from apps.sage_intacct.actions import patch_integration_settings


def assert_valid(condition: bool, message: str) -> Response or None:
    """
    Assert conditions
    :param condition: Boolean condition
    :param message: Bad request message
    :return: Response or None
    """
    if not condition:
        raise ValidationError(detail={
            'message': message
        })

class LookupFieldMixin:
    lookup_field = 'workspace_id'

    def filter_queryset(self, queryset):
        if self.lookup_field in self.kwargs:
            lookup_value = self.kwargs[self.lookup_field]
            filter_kwargs = {self.lookup_field: lookup_value}
            queryset = queryset.filter(**filter_kwargs)
        return super().filter_queryset(queryset)


def invalidate_sage_intacct_credentials(workspace_id, sage_intacct_credentials=None):
    if not sage_intacct_credentials:
        sage_intacct_credentials = SageIntacctCredential.objects.filter(workspace_id=workspace_id, is_expired=False).first()

    if sage_intacct_credentials:
        if not sage_intacct_credentials.is_expired:
            # TODO: Uncomment this when we have a FE Changes ready
            # patch_integration_settings(workspace_id, is_token_expired=True)
            pass
        sage_intacct_credentials.is_expired = True
        sage_intacct_credentials.save()
