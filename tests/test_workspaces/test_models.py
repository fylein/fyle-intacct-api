# Tests for models.py in workspaces app
from apps.workspaces.models import get_default_memo_fields


def test_get_default_memo_fields():
    expected_fields = ['employee_email', 'category', 'spent_on', 'report_number', 'purpose', 'expense_link']
    actual_fields = get_default_memo_fields()
    assert actual_fields == expected_fields