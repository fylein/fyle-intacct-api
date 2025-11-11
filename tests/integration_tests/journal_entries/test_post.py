import pytest
from tests.integration_tests.base.base_test_post import BaseTestPost
from tests.integration_tests.journal_entries.fixtures import (
    REST_JOURNAL_ENTRY_CREATE_PAYLOAD,
    SOAP_JOURNAL_ENTRY_CREATE_PAYLOAD
)


@pytest.mark.integration
class TestJournalEntriesPost(BaseTestPost):
    """
    Test journal entries POST operations.
    """
    REST_MODULE_NAME = 'journal_entries'
    SOAP_MODULE_NAME = 'journal_entries'
    REST_FIELDS = ['glJournal.id', 'description']
    SOAP_FIELDS = ['JOURNAL', 'BATCH_TITLE']
    REST_PAYLOAD = REST_JOURNAL_ENTRY_CREATE_PAYLOAD
    SOAP_PAYLOAD = SOAP_JOURNAL_ENTRY_CREATE_PAYLOAD
    KEY_MAPPINGS = [
        {
            'rest': 'glJournal.id',
            'soap': 'JOURNAL'
        },
        {
            'rest': 'description',
            'soap': 'BATCH_TITLE'
        }
    ]

    def get_soap_object_id(self, response: dict) -> str:
        """
        Get SOAP journal entry ID from POST response.
        :param response: SOAP POST response
        :return: Journal Entry ID
        """
        return response['data']['glbatch']['RECORDNO']

    def get_soap_get_parameters(self, object_id: str) -> dict:
        """
        Get SOAP GET parameters for journal entry.
        :param object_id: Journal Entry ID
        :return: SOAP GET parameters
        """
        return {
            'field': 'RECORDNO',
            'value': object_id
        }
