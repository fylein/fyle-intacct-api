"""
Workspace Serializers
"""
from rest_framework import serializers

from .models import Workspace, FyleCredential, SageIntacctCredential


class WorkspaceSerializer(serializers.ModelSerializer):
    """
    Workspace serializer
    """
    class Meta:
        model = Workspace
        fields = '__all__'


class FyleCredentialSerializer(serializers.ModelSerializer):
    """
    Fyle credential serializer
    """
    class Meta:
        model = FyleCredential
        fields = '__all__'


class SageIntacctCredentialSerializer(serializers.ModelSerializer):
    """
    Sage Intacct credential serializer
    """
    class Meta:
        model = SageIntacctCredential
        fields = ['id', 'si_user_id', 'si_company_id', 'created_at', 'updated_at', 'workspace_id']
