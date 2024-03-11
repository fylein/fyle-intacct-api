from apps.sage_intacct.errors.helpers import remove_support_id
from apps.tasks.models import Error

errors_count = Error.objects.filter(type='INTACCT_ERROR').count()
print(errors_count)

count = 0
page_size = 200
for offset in range(0, errors_count, page_size):
    limit = offset + page_size
    paginated_errors = Error.objects.filter(type='INTACCT_ERROR').order_by('id')[offset:limit]

    for error in paginated_errors:
        err_msg = error.error_detail
        err_msg = remove_support_id(err_msg)
        error.error_detail = err_msg
        error.save()
        count += 1
print(count)
