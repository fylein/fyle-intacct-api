# THIS FILE WILL BE REMOVED ONCE WE HANDLE THE EXCEPTION, KEPT IT AS A SNIPPET TO NOT MISS IT

import_log = None

# if there is an exception
import_log.status = 'FAILED'
# add exception to existing error log (maintain it as a list so that we store logs of all batches) TODO: add some max limit to the list so that it doesn't grow indefinitely for same error happening for 500 batches
import_log.error_log = import_log.error_log.append(['exception response'])

import_log.processed_batches_count += 1
import_log.queued_batches_count -= 1

import_log.save()
