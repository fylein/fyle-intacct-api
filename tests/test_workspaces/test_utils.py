import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from apps.workspaces.utils import send_email


@pytest.fixture
def mock_sendgrid():
    with patch('apps.workspaces.utils.SendGridAPIClient') as mock_sg, \
         patch('apps.workspaces.utils.Mail') as mock_mail:
        mock_instance = MagicMock()
        mock_sg.return_value = mock_instance
        mock_mail_instance = MagicMock()
        mock_mail.return_value = mock_mail_instance
        yield mock_sg, mock_mail


def test_send_email(mock_sendgrid):
    mock_sg, mock_mail = mock_sendgrid
    
    # Test data
    recipient_email = ['test@example.com']
    subject = 'Test Subject'
    message = '<p>Test Message</p>'
    sender_email = 'sender@example.com'
    
    # Mock settings
    settings.SENDGRID_API_KEY = 'test_api_key'
    
    # Call the function
    send_email(recipient_email, subject, message, sender_email)
    
    # Verify SendGridAPIClient was initialized with correct API key
    mock_sg.assert_called_once_with(api_key='test_api_key')
    
    # Verify Mail was created with correct parameters
    mock_mail.assert_called_once()
    mail_args = mock_mail.call_args[1]
    assert mail_args['to_emails'] == recipient_email
    assert mail_args['subject'] == subject
    assert mail_args['html_content'] == message
    assert mail_args['from_email'].email == sender_email
    
    # Verify mail was sent
    mock_sg.return_value.send.assert_called_once_with(mock_mail.return_value) 