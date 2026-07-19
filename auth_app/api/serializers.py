from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from rest_framework import serializers

from auth_app.services import authenticate_user


User = get_user_model()

GENERIC_INPUT_ERROR = "Please check your input and try again."
GENERIC_LOGIN_ERROR = "Please check your credentials and try again."


class RegistrationSerializer(serializers.Serializer):
    """Validate registration data and prevent duplicate accounts."""

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )
    confirmed_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate_email(self, value):
        email = value.strip().lower()
        email_exists = User.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email)
        ).exists()

        if email_exists:
            raise serializers.ValidationError(GENERIC_INPUT_ERROR)

        return email

    def validate(self, attributes):
        password = attributes["password"]
        confirmed_password = attributes["confirmed_password"]

        if password != confirmed_password:
            raise serializers.ValidationError(GENERIC_INPUT_ERROR)

        return attributes


class LoginSerializer(serializers.Serializer):
    """Authenticate users with their email address and password."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attributes):
        user = authenticate_user(
            attributes["email"],
            attributes["password"],
        )

        if user is None:
            raise serializers.ValidationError(GENERIC_LOGIN_ERROR)

        attributes["user"] = user
        return attributes


class PasswordResetRequestSerializer(serializers.Serializer):
    """Validate the email address used for a password reset request."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Validate and compare the new password fields."""

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
    )
    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate(self, attributes):
        new_password = attributes["new_password"]
        confirm_password = attributes["confirm_password"]

        if new_password != confirm_password:
            raise serializers.ValidationError(GENERIC_INPUT_ERROR)

        return attributes
