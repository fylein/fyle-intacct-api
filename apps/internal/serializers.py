from rest_framework import serializers
from apps.workspaces.models import Workspace


class E2ESetupSerializer(serializers.Serializer):
    """Serializer for E2E Setup API payload validation"""
    admin_email = serializers.EmailField(required=True, help_text="Admin email address")
    user_id = serializers.IntegerField(required=True, help_text="User ID")
    refresh_token = serializers.CharField(required=True, help_text="Refresh token")
    org_id = serializers.CharField(required=True, help_text="Organization ID")
    cluster_domain = serializers.CharField(required=True, help_text="Cluster domain")

    def validate_admin_email(self, value):
        """Validate admin email format"""
        if not value:
            raise serializers.ValidationError("Admin email is required")
        return value

    def validate_user_id(self, value):
        """Validate user ID"""
        if not value or value <= 0:
            raise serializers.ValidationError("Valid user ID is required")
        return value

    def validate_refresh_token(self, value):
        """Validate refresh token"""
        if not value or not value.strip():
            raise serializers.ValidationError("Refresh token is required")
        return value

    def validate_org_id(self, value):
        """Validate organization ID"""
        if not value or not value.strip():
            raise serializers.ValidationError("Organization ID is required")
        return value

    def validate_cluster_domain(self, value):
        """Validate cluster domain"""
        if not value or not value.strip():
            raise serializers.ValidationError("Cluster domain is required")
        return value


class E2EDestroySerializer(serializers.Serializer):
    """Serializer for E2E Destroy API payload validation"""
    org_id = serializers.CharField(required=True, help_text="Organization ID to destroy")

    # Safety constants for allowed workspace names
    ALLOWED_WORKSPACE_NAMES = [
        'E2E Integration Tests',
        'E2E Integration Test',  # Alternative naming
        'Integration Tests'      # Shorter version
    ]

    def validate_org_id(self, value):
        """Validate organization ID and perform safety checks"""
        if not value or not value.strip():
            raise serializers.ValidationError("Organization ID is required")

        # Find and validate workspace
        try:
            workspace = Workspace.objects.get(fyle_org_id=value)
        except Workspace.DoesNotExist:
            raise serializers.ValidationError(f"No workspace found for org_id: {value}")

        # CRITICAL SAFETY CHECK: Validate workspace name
        if workspace.name not in self.ALLOWED_WORKSPACE_NAMES:
            raise serializers.ValidationError(
                f"Safety check failed: Workspace name '{workspace.name}' is not in allowed list for deletion. "
                f"Only test workspaces can be deleted. Allowed names: {self.ALLOWED_WORKSPACE_NAMES}"
            )

        return value
