import time

from django_q.tasks import Chain

from fyle_accounting_mappings.models import MappingSetting


IMPORT_TASK_TARGET_MAP = {
    'PROJECT': 'Project',
    'TAX_GROUP': 'TaxGroup',
}


def chain_import_fields_to_fyle(workspace_id):
    mapping_settings = MappingSetting.objects.filter(workspace_id=workspace_id, import_to_fyle=True)
    chain = Chain()

    # TODO: we should also chain import vendors as merchants
    for mapping_setting in mapping_settings:
        # https://github.com/Koed00/django-q/issues/463
        chain.append(
            'apps.mappings.new_tasks.{}'.format(IMPORT_TASK_TARGET_MAP[mapping_setting.source_field]),
            workspace_id,
            mapping_setting.destination_field
        )

    if chain.length() > 0:
        chain.run()
