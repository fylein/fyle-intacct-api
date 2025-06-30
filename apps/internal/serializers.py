from rest_framework import serializers

from apps.workspaces.models import Workspace


class E2ESetupSerializer(serializers.Serializer):
    """Serializer for E2E Setup API payload validation"""
    workspace_id = serializers.IntegerField(required=True, help_text="Workspace ID")

    def validate_workspace_id(self, value: int) -> int:
        """Validate workspace ID"""
        if not value or value <= 0:
            raise serializers.ValidationError("Valid workspace ID is required")
        return value


class E2EDestroySerializer(serializers.Serializer):
    """Serializer for E2E Destroy API payload validation"""
    org_id = serializers.CharField(required=True, help_text="Org ID to destroy")

    # Safety constants for allowed workspace names
    ALLOWED_WORKSPACE_NAMES = [
        'E2E Integration Tests',
        'E2E Integration Test',  # Alternative naming
        'Integration Tests'      # Shorter version
    ]

    def validate_org_id(self, value: str) -> str:
        """Validate org ID and perform safety checks"""
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
