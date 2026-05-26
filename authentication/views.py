from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PasswordResetOTP
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ─── REGISTER ─────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new customer or driver account.

    Body (customer):
        full_name, email, phone_number, password, confirm_password,
        user_type="customer", location, referral_code (optional)

    Body (driver) — adds:
        user_type="driver", vehicle_type, vehicle_number, license_number
    """
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'message': 'Validation failed.', 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = serializer.save()
    tokens = get_tokens_for_user(user)

    return Response(
        {
            'success': True,
            'message': 'Account created successfully! Please log in.',
            'user': UserSerializer(user).data,
            'tokens': tokens,
        },
        status=status.HTTP_201_CREATED,
    )


# authentication/views.py - Updated login() function
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'message': 'Invalid input.', 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    identifier = serializer.validated_data['email_or_phone'].lower().strip()
    password = serializer.validated_data['password']
    ip_address = request.META.get('REMOTE_ADDR')

    # 🔒 Check if account is locked
    is_locked, lock_msg = LoginAttempt.check_lockout(identifier)
    if is_locked:
        return Response(
            {'success': False, 'message': lock_msg},
            status=status.HTTP_423_LOCKED,
        )

    # Find user by email OR phone
    user = (
        User.objects.filter(email__iexact=identifier).first()
        or User.objects.filter(phone_number=identifier.replace(' ', '').replace('-', '')).first()
    )

    if user is None or not user.check_password(password):
        # Record failed attempt
        LoginAttempt.record_failure(identifier, ip_address)
        return Response(
            {'success': False, 'message': 'Invalid credentials. Please check your email/phone and password.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {'success': False, 'message': 'Your account has been deactivated. Please contact support.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    # ✅ Success: Reset attempts & return tokens
    LoginAttempt.reset_attempts(identifier)
    tokens = get_tokens_for_user(user)

    return Response(
        {
            'success': True,
            'message': 'Login successful.',
            'user': UserSerializer(user).data,
            'access': tokens['access'],   # ✅ Flat structure for Flutter
            'refresh': tokens['refresh'],
        },
        status=status.HTTP_200_OK,
    )

# ─── FORGOT PASSWORD ──────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """
    Request a 6-digit OTP reset code.

    Body:
        email

    Returns:
        200 always (security — don't leak whether email exists)
        debug_token included in dev mode (DEBUG=True) so you can test without email
    """
    serializer = ForgotPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'message': 'Invalid input.', 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    email = serializer.validated_data['email']
    user  = User.objects.filter(email__iexact=email).first()

    response_data = {
        'success': True,
        'message': 'If that email exists in our system, a reset code has been sent.',
    }

    if user:
        otp = PasswordResetOTP.generate_for(user)

        # Send email (goes to console in dev)
        try:
            send_mail(
                subject='FuelConnect — Your Password Reset Code',
                message=(
                    f'Hi {user.full_name},\n\n'
                    f'Your 6-digit password reset code is: {otp.otp_code}\n\n'
                    f'This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n\n'
                    f'If you did not request this, please ignore this email.\n\n'
                    f'— The FuelConnect Team'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass  # Never break the flow because of email

        # Expose OTP in debug mode so Bruno / Flutter emulator can test
        if settings.DEBUG:
            response_data['debug_token'] = otp.otp_code
            response_data['debug_note'] = 'debug_token is only present when DEBUG=True'

    return Response(response_data, status=status.HTTP_200_OK)


# ─── RESET PASSWORD ───────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Verify OTP and set a new password.

    Body:
        email
        token            — the 6-digit code
        new_password
        confirm_new_password
    """
    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'message': 'Validation failed.', 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    email       = serializer.validated_data['email']
    otp_code    = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return Response(
            {'success': False, 'message': 'Invalid or expired reset code.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    otp = PasswordResetOTP.objects.filter(
        user=user, otp_code=otp_code, is_used=False
    ).order_by('-created_at').first()

    if not otp:
        return Response(
            {'success': False, 'message': 'Invalid or expired reset code.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if otp.is_expired():
        return Response(
            {'success': False, 'message': 'This reset code has expired. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(new_password)
    user.save()
    otp.is_used = True
    otp.save()

    return Response(
        {'success': True, 'message': 'Password reset successfully. You can now log in.'},
        status=status.HTTP_200_OK,
    )


# ─── ME (protected) ───────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Return the currently authenticated user's profile.
    Requires: Authorization: Bearer <access_token>
    """
    return Response(
        {'success': True, 'user': UserSerializer(request.user).data},
        status=status.HTTP_200_OK,
    )


# ─── REFRESH TOKEN ────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Exchange a refresh token for a new access token.

    Body:
        refresh
    """
    from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
    try:
        refresh = RefreshToken(request.data.get('refresh', ''))
        return Response(
            {'success': True, 'access': str(refresh.access_token)},
            status=status.HTTP_200_OK,
        )
    except (TokenError, InvalidToken):
        return Response(
            {'success': False, 'message': 'Invalid or expired refresh token.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
