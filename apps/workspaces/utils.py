from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From


def send_email(recipient_email: list[str], subject: str, message: str, sender_email: str) -> None:
    """
    Email to the user using sendgrid-sdk
    :param recipient_email: (List[str])
    :param subject: (str)
    :param message: (str)
    :param sender_email: (str)
    :return: None
    """
    SENDGRID_API_KEY = settings.SENDGRID_API_KEY
    sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
    from_email = From(email=sender_email)
    mail = Mail(
        from_email=from_email,
        to_emails=recipient_email,
        subject=subject,
        html_content=message
    )
    sg.send(mail)
