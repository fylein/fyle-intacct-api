import json
import logging
from typing import Optional

import requests
from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework.serializers import ValidationError
from rest_framework.views import Response

from apps.workspaces.models import SageIntacctCredential

logger = logging.getLogger(__name__)
logger.level = logging.INFO


def post_request(url: str, body: dict, refresh_token: str = None) -> Optional[dict]:
    """
    Create a HTTP post request.
    :param url: URL
    :param body: Body
    :param refresh_token: Refresh token
    :return: dict
    """
    access_token = None
    api_headers = {
        'content-type': 'application/json'
    }
    if refresh_token:
        access_token = get_access_token(refresh_token)

        api_headers['Authorization'] = 'Bearer {0}'.format(access_token)

    response = requests.post(
        url,
        headers=api_headers,
        data=json.dumps(body)
    )

    if response.status_code in [200, 201]:
        return json.loads(response.text)
    else:
        raise Exception(response.text)


def patch_request(url: str, body: dict, refresh_token: Optional[str] = None) -> Optional[dict]:
    """
    Create a HTTP patch request.
    """
    access_token = None
    api_headers = {
        'Content-Type': 'application/json',
    }
    if refresh_token:
        access_token = get_access_token(refresh_token)

        api_headers['Authorization'] = 'Bearer {0}'.format(access_token)

    response = requests.patch(
        url,
        headers=api_headers,
        data=json.dumps(body)
    )

    if response.status_code in [200, 201]:
        return json.loads(response.text)
    else:
        raise Exception(response.text)


def get_access_token(refresh_token: str) -> str:
    """
    Get access token from fyle
    :param refresh_token: Refresh token
    :return: Access token
    """
    api_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': settings.FYLE_CLIENT_ID,
        'client_secret': settings.FYLE_CLIENT_SECRET
    }

    return post_request(settings.FYLE_TOKEN_URI, body=api_data)['access_token']


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
            import_string('apps.workspaces.tasks.patch_integration_settings')(workspace_id, is_token_expired=True)
        
        sage_intacct_credentials.access_token = None
        sage_intacct_credentials.access_token_expires_at = None
        sage_intacct_credentials.save()
