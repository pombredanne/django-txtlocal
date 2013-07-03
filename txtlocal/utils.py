import requests

from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.utils.http import urlencode


def send_sms(text, recipient_list, sender=None,
             username=None, password=None, **kwargs):
    """
    Render and send an SMS template.

    The current site will be added to any context dict passed.

        recipient_list: A list of number strings. Each number must be purely
                        numeric, so no '+' symbols, hyphens or spaces. The
                        numbers must be prefixed with their international
                        dialling codes.
                        eg. UK numbers would look like 447123456789.
        text: The message text. (Gets URI encoded.)
        sender: Must be word up to 11 characters or a number up to 14 digits.
                Defaults to settings.DEFAULT_FROM_SMS. (Must be a string.)
        username: Defaults to settings.TXTLOCAL_USERNAME.
        password: Defaults to settings.TXTLOCAL_PASSWORD.
        **kwargs: Will be passed through to textlocal in the POST data.

    Any unrecognised kwargs will be passed to txtlocal in the POST data.
    """
    post_data = {
        'selectednums': ','.join(recipient_list),
        'message': urlencode(text),
        'uname': username or settings.TXTLOCAL_USERNAME,
        'pword': password or password.TXTLOCAL_PASSWORD,
        'from': sender or settings.DEFAULT_FROM_SMS,
        'json': 1,  # This makes textlocal send us back info about the request.
    }

    url = "http://www.txtlocal.com/sendsmspost.php"
    response = requests.post(url, data=post_data).json()
    available = response.get('CreditsAvailable')
    required = response.get('CreditsRequired')
    remaining = response.get('CreditsRemaining')
    if (
        available is None or
        required is None or
        remaining is None or
        required <= 0 or
        available - required != remaining
    ):
        err = 'Message may not have been sent. Response was: "%s"' % response
        raise RuntimeError(err)


def render_to_send_sms(template, context=None, **kwargs):
    """
    Render and send an SMS template.

    The current site will be added to any context dict passed.

    Any unrecognised kwargs will be passed to send_sms.
    """
    if context is None:
        context = {}
    context['site'] = Site.objects.get_current()
    text = render_to_string(template, context)

    send_sms(text, **kwargs)
