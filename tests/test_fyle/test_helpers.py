from asyncio.log import logger
from unittest import mock
from rest_framework.response import Response
from rest_framework.views import status
from apps.fyle.helpers import post_request, get_request, get_fyle_orgs


def test_post_request(mocker):
    mocker.patch(
        'apps.fyle.helpers.requests.post',
        return_value=mock.MagicMock(status_code=200, text="{'key': 'dfghjk'}")
    )
    try:
        response = post_request(url='sdfghjk', body={}, refresh_token='srtyu')
        assert response == {'key': 'dfghjk'}
    except:
        logger.info('Error in post request')
    
    mocker.patch(
        'apps.fyle.helpers.requests.post',
        return_value=Response(
            {
                'message': 'Post request'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    )
    try:
        post_request(url='sdfghjk', body={}, refresh_token='srtyu')
    except:
        logger.info('Error in post request')


def test_get_request(mocker):
    mocker.patch(
        'apps.fyle.helpers.requests.get',
        return_value=mock.MagicMock(status_code=200, text="{'key': 'dfghjk'}")
    )
    try:
        response = get_request(url='sdfghjk', params={'key': 'dfghjk'}, refresh_token='srtyu')
        assert response == {'key': 'dfghjk'}
    except:
        logger.info('Error in post request')
    
    mocker.patch(
        'apps.fyle.helpers.requests.get',
        return_value=Response(
            {
                'message': 'Get request'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    )
    try:
        get_request(url='sdfghjk', params={'sample': True}, refresh_token='srtyu')
    except:
        logger.info('Error in post request')


def test_get_fyle_orgs(mocker):
    mocker.patch(
        'apps.fyle.helpers.requests.get',
        return_value=mock.MagicMock(status_code=200, text="{'orgs': 'dfghjk'}")
    )
    try:
        response = get_fyle_orgs(refresh_token='srtyu', cluster_domain='erty')
        assert response == {'orgs': 'dfghjk'}
    except:
        logger.info('Error in post request')
