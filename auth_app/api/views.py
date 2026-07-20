from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from auth_app.api.serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegistrationSerializer,
)
from auth_app.services import (
    activate_user,
    blacklist_refresh_token,
    confirm_password_reset,
    create_token_pair,
    refresh_token_pair,
    register_user,
    request_password_reset,
)
from auth_app.utils import (
    delete_auth_cookies,
    set_access_cookie,
    set_auth_cookies,
    set_refresh_cookie,
)


class RegisterView(APIView):
    """Create an inactive user account and send an activation email."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        register_user(serializer.validated_data)
        return Response(
            {
                "detail": (
                    "Registration successful. "
                    "Please check your email to activate your account."
                )
            },
            status=status.HTTP_201_CREATED,
        )


class ActivateAccountView(APIView):
    """Activate a user account with its encoded ID and activation token."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        activation_successful = activate_user(uidb64, token)
        if not activation_successful:
            return Response(
                {"detail": "Account activation failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"message": "Account successfully activated."},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    """Authenticate a user and store the JWT pair in HttpOnly cookies."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        access_token, refresh_token = create_token_pair(user)
        response_data = {
            "detail": "Login successful",
            "user": {"id": user.id, "username": user.username},
        }
        response = Response(response_data, status=status.HTTP_200_OK)
        set_auth_cookies(response, access_token, refresh_token)
        return response


class RefreshTokenView(APIView):
    """Create fresh JWT credentials from the refresh-token cookie."""

    authentication_classes = []
    permission_classes = [AllowAny]

    # The refresh token is stored in an HttpOnly cookie, not in the request body.
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return self.missing_token_response()
        try:
            tokens = refresh_token_pair(refresh_token)
        except (InvalidToken, TokenError):
            return self.invalid_token_response()
        return self.success_response(tokens)

    @staticmethod
    def missing_token_response():
        return Response(
            {"detail": "Refresh token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @staticmethod
    def invalid_token_response():
        return Response(
            {"detail": "Invalid refresh token."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    @staticmethod
    def success_response(tokens):
        response_data = {
            "detail": "Token refreshed",
            "access": tokens["access"],
        }
        response = Response(response_data, status=status.HTTP_200_OK)
        set_access_cookie(response, tokens["access"])
        if tokens.get("refresh"):
            set_refresh_cookie(response, tokens["refresh"])
        return response


class LogoutView(APIView):
    """Blacklist the refresh token when possible and clear auth cookies."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                blacklist_refresh_token(refresh_token)
            except TokenError:
                pass
        return self.success_response()

    @staticmethod
    def success_response():
        detail = "Logout successful. Authentication cookies were deleted."
        response = Response(
            {"detail": detail},
            status=status.HTTP_200_OK,
        )
        delete_auth_cookies(response)
        return response


class PasswordResetRequestView(APIView):
    """Request a password-reset email without revealing account existence."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_password_reset(serializer.validated_data["email"])
        return Response(
            {"detail": "An email has been sent to reset your password."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Validate reset credentials and store the user's new password."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data["new_password"]
        reset_successful = confirm_password_reset(uidb64, token, new_password)
        if not reset_successful:
            return Response(
                {"detail": "Password reset failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"detail": "Your password has been successfully reset."},
            status=status.HTTP_200_OK,
        )
