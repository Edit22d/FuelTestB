import re

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

# safe import (prevents crash if app loads before models fully ready)
try:
    from authentication.models import DriverProfile
except Exception:
    DriverProfile = None


# ──────────────────────────────────────────────────────────────
# REGEX
# ──────────────────────────────────────────────────────────────

PHONE_RE = re.compile(r'^\+?[\d\s\-]{9,15}$')

PASS_RE = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
)


# ──────────────────────────────────────────────────────────────
# REGISTER SERIALIZER
# ──────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.Serializer):

    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()

    phone_number = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    user_type = serializers.ChoiceField(
        choices=['customer', 'driver'],
        default='customer'
    )

    location = serializers.CharField(required=False, allow_blank=True)

    referral_code = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    vehicle_type = serializers.CharField(required=False, allow_blank=True)
    vehicle_number = serializers.CharField(required=False, allow_blank=True)
    license_number = serializers.CharField(required=False, allow_blank=True)

    company_name = serializers.CharField(required=False, allow_blank=True)
    fleet_size = serializers.IntegerField(required=False, default=0)

    # ─────────────────────────────────────────────
    # VALIDATION
    # ─────────────────────────────────────────────

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate_phone_number(self, value):
        if not value:
            return ""

        value = value.strip()

        if not PHONE_RE.match(value):
            raise serializers.ValidationError("Invalid phone number format.")

        # normalize
        normalized = re.sub(r'[\s\-]', '', value)

        for user in User.objects.exclude(phone_number__isnull=True).exclude(phone_number=""):
            if re.sub(r'[\s\-]', '', user.phone_number) == normalized:
                raise serializers.ValidationError("Phone number already exists.")

        return value

    def validate_password(self, value):
        if not PASS_RE.match(value):
            raise serializers.ValidationError(
                "Password must include uppercase, lowercase, number and symbol."
            )
        return value

    def validate(self, attrs):

        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        if attrs.get("user_type") == "driver":
            if not attrs.get("vehicle_type"):
                raise serializers.ValidationError({"vehicle_type": "Required for driver"})
            if not attrs.get("vehicle_number"):
                raise serializers.ValidationError({"vehicle_number": "Required for driver"})

        return attrs

    # ─────────────────────────────────────────────
    # CREATE USER
    # ─────────────────────────────────────────────

    def create(self, validated_data):

        validated_data.pop("confirm_password")

        password = validated_data.pop("password")

        vehicle_type = validated_data.pop("vehicle_type", "")
        vehicle_number = validated_data.pop("vehicle_number", "")
        license_number = validated_data.pop("license_number", "")

        # FIX: avoid empty string causing UNIQUE errors
        referral_code = validated_data.get("referral_code")
        if not referral_code:
            validated_data["referral_code"] = None

        validated_data.setdefault("company_name", "")
        validated_data.setdefault("fleet_size", 0)
        validated_data.setdefault("auth_provider", "email")

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # create driver profile safely
        if (
            user.user_type == "driver"
            and DriverProfile
            and vehicle_type
        ):
            DriverProfile.objects.create(
                user=user,
                vehicle_type=vehicle_type,
                vehicle_number=vehicle_number,
                license_number=license_number,
            )

        return user


# ──────────────────────────────────────────────────────────────
# LOGIN SERIALIZER
# ──────────────────────────────────────────────────────────────
class LoginSerializer(serializers.Serializer):

    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_phone_number(self, value):
        return value.strip()


# ──────────────────────────────────────────────────────────────
# FORGOT PASSWORD
# ──────────────────────────────────────────────────────────────

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


# ──────────────────────────────────────────────────────────────
# RESET PASSWORD
# ──────────────────────────────────────────────────────────────

class ResetPasswordSerializer(serializers.Serializer):

    email = serializers.EmailField()
    token = serializers.CharField(min_length=6, max_length=6)

    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        if not PASS_RE.match(value):
            raise serializers.ValidationError(
                "Password must include uppercase, lowercase, number, symbol."
            )
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_new_password"]:
            raise serializers.ValidationError({
                "confirm_new_password": "Passwords do not match."
            })
        return attrs


# ──────────────────────────────────────────────────────────────
# USER SERIALIZER
# ──────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):

    driver_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "company_name",
            "fleet_size",
            "is_email_verified",
            "auth_provider",
            "user_type",
            "location",
            "date_joined",
            "is_active",
            "driver_profile",
        ]

    def get_driver_profile(self, obj):

        if obj.user_type == "driver" and hasattr(obj, "driver_profile"):
            dp = obj.driver_profile
            return {
                "vehicle_type": dp.vehicle_type,
                "vehicle_number": dp.vehicle_number,
                "license_number": dp.license_number,
                "is_verified": dp.is_verified,
            }

        return None