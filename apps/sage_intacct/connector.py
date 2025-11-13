from typing import Optional
from datetime import datetime, timedelta, timezone

from django.db.models import Q
from django.conf import settings

from intacctsdk import IntacctRESTSDK

from apps.mappings.models import LocationEntityMapping
from apps.workspaces.models import SageIntacctCredential


class SageIntacctRestConnector:
    """
    Sage Intacct REST connector
    """
    def __init__(self, workspace_id: int):
        """
        Initialize the Sage Intacct REST connector
        :param workspace_id: Workspace ID
        """
        self.workspace_id = workspace_id
        self.credential_object = self.__get_credential_object()

        self.access_token = self.__get_access_token()
        self.refresh_token = self.__get_refresh_token()
        self.location_entity_id = self.__get_location_entity_id()

        self.connection = IntacctRESTSDK(
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            entity_id=self.location_entity_id,
            client_id=settings.INTACCT_CLIENT_ID,
            client_secret=settings.INTACCT_CLIENT_SECRET
        )

        if not self.access_token:
            self.__update_tokens(
                access_token=self.connection.access_token,
                refresh_token=self.connection.refresh_token
            )

    def __get_credential_object(self) -> Optional[SageIntacctCredential]:
        """
        Get credential object
        :return: Optional[SageIntacctCredential]
        """
        return SageIntacctCredential.get_active_sage_intacct_credentials(workspace_id=self.workspace_id)

    def __get_access_token(self) -> Optional[str]:
        """
        Get access token
        :return: Optional[str]
        """
        if (
            self.credential_object
            and self.credential_object.access_token
            and self.credential_object.access_token_expires_at > datetime.now(timezone.utc)
        ):
            return self.credential_object.access_token

        return None

    def __get_refresh_token(self) -> Optional[str]:
        """
        Get refresh token
        :return: Optional[str]
        """
        if self.credential_object and self.credential_object.refresh_token:
            return self.credential_object.refresh_token

        return None

    def __get_location_entity_id(self) -> Optional[str]:
        """
        Get location entity id
        :return: Optional[str]
        """
        location_entity_mapping = LocationEntityMapping.objects.filter(
            ~Q(destination_id='top_level'), workspace_id=self.workspace_id
        ).first()
        return location_entity_mapping.destination_id if location_entity_mapping else None

    def __update_tokens(
        self,
        access_token: str,
        refresh_token: str
    ) -> None:
        """
        Update tokens
        :param access_token: Access token
        :param refresh_token: Refresh token
        :return: None
        """
        ACCESS_TOKEN_EXPIRATION_TIME = 4  # 4 hours (access token expires in 6 hours)
        self.credential_object.refresh_from_db()
        self.credential_object.access_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRATION_TIME)
        self.credential_object.access_token = access_token
        self.credential_object.refresh_token = refresh_token
        self.credential_object.save(update_fields=[
            'access_token_expires_at',
            'access_token',
            'refresh_token',
            'updated_at',
        ])
