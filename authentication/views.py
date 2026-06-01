from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .models import PasswordResetOTP, LoginAttempt
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)

User = get_user_model()


# =========================================================
# TOKENS
# =========================================================
def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# =========================================================
# APP INFO (FIXED 404 ISSUE)
# =========================================================
@api_view(["GET"])
@permission_classes([AllowAny])
def app_info(request):
    return Response({
        "success": True,
        "app_name": "FuelConnect",
        "version": "1.0.0",
        "status": "running"
    })


# =========================================================
# REGISTER (FIXED SAFE VERSION)
# =========================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):

    serializer = RegisterSerializer(data=request.data)

    # 🔴 PUT IT HERE (RIGHT AFTER CREATING SERIALIZER)
    if not serializer.is_valid():
        print(serializer.errors)  # 👈 ADD THIS LINE FOR DEBUGGING

        return Response({
            "success": False,
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=400)

    try:
        user = serializer.save()
        tokens = get_tokens(user)

        return Response({
            "success": True,
            "message": "Account created successfully",
            "user": UserSerializer(user).data,
            "tokens": tokens
        }, status=201)

    except Exception as e:
        return Response({
            "success": False,
            "message": str(e)
        }, status=500)


# =========================================================
# LOGIN (FIXED IDENTIFIER HANDLING)
# =========================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    print(request.data)

    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            "success": False,
            "message": "Invalid input",
            "errors": serializer.errors
        }, status=400)
    

    phone_number = serializer.validated_data["phone_number"]
    password = serializer.validated_data["password"]

    # normalize phone number
    phone_clean = (
        phone_number
        .replace(" ", "")
        .replace("-", "")
        .strip()
    )

    ip = request.META.get("REMOTE_ADDR")

    # check lock
    locked, msg = LoginAttempt.check_lockout(phone_clean)

    if locked:
        return Response({
            "success": False,
            "message": msg
        }, status=423)

    # find user
    user = User.objects.filter(
        phone_number=phone_clean
    ).first()

    # invalid credentials
    if not user or not user.check_password(password):

        LoginAttempt.record_failure(phone_clean, ip)

        return Response({
            "success": False,
            "message": "Invalid phone number or password"
        }, status=401)

    # inactive account
    if not user.is_active:
        return Response({
            "success": False,
            "message": "Account disabled"
        }, status=403)

    # clear failed attempts
    LoginAttempt.objects.filter(
        identifier=phone_clean
    ).delete()

    return Response({
        "success": True,
        "message": "Login successful",
        "user": UserSerializer(user).data,
        "tokens": get_tokens(user)
    })

# =========================================================
# FORGOT PASSWORD
# =========================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):

    serializer = ForgotPasswordSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            "success": False,
            "message": "Invalid input",
            "errors": serializer.errors
        }, status=400)

    email = serializer.validated_data["email"]
    user = User.objects.filter(email__iexact=email).first()

    response = {
        "success": True,
        "message": "If account exists, OTP sent"
    }

    if user:
        otp = PasswordResetOTP.create_otp(
            user,
            expiry_minutes=getattr(settings, "OTP_EXPIRY_MINUTES", 10)
        )

        try:
            send_mail(
                "FuelConnect OTP",
                f"Your OTP is {otp.otp_code}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True
            )
        except:
            pass

        if settings.DEBUG:
            response["debug_otp"] = otp.otp_code

    return Response(response)


# =========================================================
# RESET PASSWORD
# =========================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):

    serializer = ResetPasswordSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            "success": False,
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=400)

    email = serializer.validated_data["email"]
    token = serializer.validated_data["token"]
    new_password = serializer.validated_data["new_password"]

    user = User.objects.filter(email__iexact=email).first()

    if not user:
        return Response({"success": False, "message": "Invalid code"}, status=400)

    otp = PasswordResetOTP.objects.filter(
        user=user,
        otp_code=token,
        is_used=False
    ).order_by("-created_at").first()

    if not otp:
        return Response({"success": False, "message": "Invalid OTP"}, status=400)

    if otp.is_expired:
        return Response({"success": False, "message": "OTP expired"}, status=400)

    user.set_password(new_password)
    user.save()

    otp.is_used = True
    otp.save()

    return Response({
        "success": True,
        "message": "Password reset successful"
    })


# =========================================================
# CURRENT USER
# =========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({
        "success": True,
        "user": UserSerializer(request.user).data
    })


# =========================================================
# REFRESH TOKEN (FIXED SAFE VERSION)
# =========================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):

    try:
        refresh = RefreshToken(request.data.get("refresh"))
        return Response({
            "success": True,
            "access": str(refresh.access_token)
        })

    except (TokenError, InvalidToken):
        return Response({
            "success": False,
            "message": "Invalid refresh token"
        }, status=401)