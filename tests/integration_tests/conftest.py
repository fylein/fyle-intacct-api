import pytest

from tests.integration_tests.base.soap_client import SoapClient
from tests.integration_tests.base.rest_client import RestClient


@pytest.fixture(scope='session')
def soap_client():
    """
    Create SOAP client for the session.
    Session-scoped to reuse connection.
    :return: SoapClient instance
    """
    return SoapClient()


@pytest.fixture(scope='session')
def rest_client():
    """
    Create REST client for the session.
    Session-scoped to reuse connection.
    :return: RestClient instance
    """
    return RestClient()
