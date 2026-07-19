from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Generate tokens that become invalid after account activation."""

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.password}{user.is_active}{timestamp}"


account_activation_token = AccountActivationTokenGenerator()


def build_activation_link(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    parameters = urlencode({"uid": uid, "token": token})

    return f"{settings.FRONTEND_ACTIVATION_URL}?{parameters}"


def set_auth_cookie(response, name, value, max_age):
    """Set an authentication cookie with shared security settings."""
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/",
    )


def set_access_cookie(response, access_token):
    set_auth_cookie(
        response,
        "access_token",
        access_token,
        settings.AUTH_COOKIE_ACCESS_MAX_AGE,
    )


def set_refresh_cookie(response, refresh_token):
    set_auth_cookie(
        response,
        "refresh_token",
        refresh_token,
        settings.AUTH_COOKIE_REFRESH_MAX_AGE,
    )


def set_auth_cookies(response, access_token, refresh_token):
    set_access_cookie(response, access_token)
    set_refresh_cookie(response, refresh_token)


def delete_auth_cookies(response):
    response.delete_cookie(
        key="access_token",
        path="/",
    )
    response.delete_cookie(
        key="refresh_token",
        path="/",
    )


def build_password_reset_link(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    parameters = urlencode({"uid": uid, "token": token})

    return f"{settings.FRONTEND_PASSWORD_RESET_URL}?{parameters}"
