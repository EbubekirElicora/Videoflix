from email.message import MIMEPart
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


LOGO_PATH = "auth_app/email/videoflix_logo.png"
LOGO_CONTENT_ID = "videoflix_logo"


def build_inline_logo(logo_path):
    """Build the inline PNG attachment for an HTML email."""
    logo = MIMEPart()
    logo.set_content(
        Path(logo_path).read_bytes(),
        maintype="image",
        subtype="png",
        disposition="inline",
        cid=f"<{LOGO_CONTENT_ID}>",
        filename="videoflix_logo.png",
    )
    return logo


def attach_logo(email):
    """Attach the Videoflix logo when the PNG file exists."""
    logo_path = finders.find(LOGO_PATH)
    if logo_path is None:
        return
    email.attach(build_inline_logo(logo_path))


def send_html_email(subject, template_name, context, text_body, recipient):
    """Render and send a multipart HTML email with an inline logo."""
    html_body = render_to_string(template_name, context)
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    attach_logo(email)
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)
