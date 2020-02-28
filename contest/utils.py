from django.contrib.auth.decorators import user_passes_test
from socketlabs.injectionapi import SocketLabsClient
from socketlabs.injectionapi.message.basicmessage import BasicMessage
from socketlabs.injectionapi.message.emailaddress import EmailAddress
from django.conf import settings
import logging
logger = logging.getLogger('got')


def verification_required(function):
    actual_decorator = user_passes_test(
        lambda u: u.is_active,
    )
    if function:
        return actual_decorator(function)
    else:
        pass
    return actual_decorator


def process_messages(request):
    """Add unread messages to Template contexts"""
    ret = {}
    if request.user.is_authenticated:
        messages = request.user.unread_messages()
        if messages:
            ret['unread_messages'] = messages

    return ret


def send_mail(subject, recipient, body, html_body=None):
    client = SocketLabsClient(int(settings.SERVER_ID), settings.INJECTION_API_KEY)
    message = BasicMessage()
    message.subject = subject
    message.html_body = html_body
    message.plain_text_body = body
    message.from_email_address = EmailAddress(settings.CONTEST_SENDER_EMAIL)
    message.to_email_address.append(EmailAddress(recipient))
    response = client.send(message)
    if response.result.name != 'Success':
        logger.error(f"Email not sent {response.result}")


