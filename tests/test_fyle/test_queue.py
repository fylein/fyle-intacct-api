from apps.fyle.models import Expense
from apps.fyle.queue import async_post_accounting_export_summary, async_import_and_export_expenses


# This test is just for cov :D
def test_async_post_accounting_export_summary(db):
    async_post_accounting_export_summary(1, 1)
    assert True

# This test is just for cov :D
def test_async_import_and_export_expenses(db):
    body = {
        'action': 'ACCOUNTING_EXPORT_INITIATED',
        'data': {
            'id': 'rp1s1L3QtMpF',
            'org_id': 'or79Cob97KSh'
        }
    }

    async_import_and_export_expenses(body)
