from django.core.cache import cache

from apps.workspaces.models import FeatureConfig, get_default_memo_fields


def test_get_default_memo_fields():
    """
    Test get_default_memo_fields function
    """
    expected_fields = ['employee_email', 'category', 'spent_on', 'report_number', 'purpose', 'expense_link']
    actual_fields = get_default_memo_fields()
    assert actual_fields == expected_fields


def test_get_feature_config_without_cache(db, add_feature_config):
    """
    Test FeatureConfig.get_feature_config method without cache
    """
    workspace_id = 1
    add_feature_config(workspace_id, export_via_rabbitmq=True, fyle_webhook_sync_enabled=False)
    cache.clear()

    result = FeatureConfig.get_feature_config(workspace_id, 'export_via_rabbitmq')
    assert result == True

    result = FeatureConfig.get_feature_config(workspace_id, 'fyle_webhook_sync_enabled')
    assert result == False


def test_get_feature_config_with_cache(db, add_feature_config):
    """
    Test FeatureConfig.get_feature_config method with cache hit
    """
    workspace_id = 1
    add_feature_config(workspace_id, export_via_rabbitmq=False, fyle_webhook_sync_enabled=True)
    cache.clear()
    result = FeatureConfig.get_feature_config(workspace_id, 'export_via_rabbitmq')
    assert result == False
    result = FeatureConfig.get_feature_config(workspace_id, 'export_via_rabbitmq')
    assert result == False
