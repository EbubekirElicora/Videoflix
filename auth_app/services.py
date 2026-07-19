from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.email_service import send_html_email
from auth_app.utils import (
    account_activation_token,
    build_activation_link,
    build_password_reset_link,
)


User = get_user_model()


def create_inactive_user(validated_data):
    """Create and store a user who must activate the account first."""
    email = validated_data["email"]
    user = User(username=email, email=email, is_active=False)
    user.set_password(validated_data["password"])
    user.save()
    return user


def build_activation_email_message(activation_link):
    """Build the plain-text fallback for the activation email."""
    return (
        "Welcome to Videoflix!\n\n"
        "Please activate your account using the following link:\n"
        f"{activation_link}"
    )


def send_activation_email(user):
    """Send a multipart account-activation email."""
    activation_link = build_activation_link(user)
    send_html_email(
        subject="Activate your Videoflix account",
        template_name="auth_app/emails/activation_email.html",
        context={"activation_link": activation_link},
        text_body=build_activation_email_message(activation_link),
        recipient=user.email,
    )


@transaction.atomic
def register_user(validated_data):
    """Create an inactive user and send the activation email."""
    user = create_inactive_user(validated_data)
    send_activation_email(user)
    return user


def get_user_by_uid(uidb64):
    """Decode a user ID and return the matching user when available."""
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def activate_user(uidb64, token):
    """Validate the activation token and enable the user account."""
    user = get_user_by_uid(uidb64)
    if user is None:
        return False
    if not account_activation_token.check_token(user, token):
        return False
    user.is_active = True
    user.save(update_fields=["is_active"])
    return True


def authenticate_user(email, password):
    """Authenticate a user with a normalized email and password."""
    normalized_email = email.strip().lower()
    return authenticate(
        username=normalized_email,
        password=password,
    )


def create_token_pair(user):
    """Create an access token and refresh token for a user."""
    refresh_token = RefreshToken.for_user(user)
    access_token = refresh_token.access_token
    return str(access_token), str(refresh_token)


def refresh_token_pair(refresh_token):
    """Validate a refresh token and return newly generated tokens."""
    serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def blacklist_refresh_token(refresh_token):
    """Blacklist a refresh token so that it cannot be reused."""
    token = RefreshToken(refresh_token)
    token.blacklist()


def get_active_user_by_email(email):
    """Return the active user associated with an email address."""
    return User.objects.filter(
        email__iexact=email.strip(),
        is_active=True,
    ).first()


def build_password_reset_email_message(reset_link):
    """Build the plain-text fallback for the password-reset email."""
    return (
        "You requested a password reset for your Videoflix account.\n\n"
        "Use the following link to set a new password:\n"
        f"{reset_link}"
    )


def send_password_reset_email(user):
    """Send a multipart password-reset email."""
    reset_link = build_password_reset_link(user)
    send_html_email(
        subject="Reset your Videoflix password",
        template_name="auth_app/emails/password_reset_email.html",
        context={"password_reset_link": reset_link},
        text_body=build_password_reset_email_message(reset_link),
        recipient=user.email,
    )


def request_password_reset(email):
    """Send a reset email without revealing whether the account exists."""
    user = get_active_user_by_email(email)
    if user is not None:
        send_password_reset_email(user)


def confirm_password_reset(uidb64, token, new_password):
    """Validate reset credentials and store the new password."""
    user = get_user_by_uid(uidb64)
    if user is None:
        return False
    if not default_token_generator.check_token(user, token):
        return False
    user.set_password(new_password)
    user.save(update_fields=["password"])
    return True
