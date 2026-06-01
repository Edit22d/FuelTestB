from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils import timezone
from datetime import timedelta
import random
import uuid


# =========================================================
# REFERRAL CODE
# =========================================================

def generate_referral_code():
    return str(uuid.uuid4()).replace("-", "")[:8].upper()


# =========================================================
# USER MANAGER
# =========================================================

class UserManager(BaseUserManager):

    def create_user(self, phone_number, password=None, email=None, **extra_fields):

        if not phone_number:
            raise ValueError("Phone number is required")

        phone_number = phone_number.replace(" ", "").strip()

        email = email.strip().lower() if email else None

        user = self.model(
            phone_number=phone_number,
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, email=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("user_type", "admin")
        extra_fields.setdefault("is_active", True)

        return self.create_user(
            phone_number=phone_number,
            password=password,
            email=email or "admin@fuelconnect.com",
            **extra_fields
        )


# =========================================================
# USER MODEL (FIXED)
# =========================================================

class User(AbstractBaseUser, PermissionsMixin):

    USER_TYPE_CHOICES = [
        ("customer", "Customer"),
        ("driver", "Driver"),
        ("admin", "Admin"),
    ]

    # ✔️ CORRECT FIELDS (NO NESTING!)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True)

    full_name = models.CharField(max_length=255, blank=True, null=True)

    company_name = models.CharField(max_length=255, blank=True, null=True)

    fleet_size = models.IntegerField(default=0)

    auth_provider = models.CharField(max_length=50, default="phone")

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default="customer"
    )

    location = models.CharField(max_length=255, blank=True, null=True)

    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    # IMPORTANT
    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.phone_number:
            self.phone_number = self.phone_number.replace(" ", "").strip()

        if not self.referral_code:
            self.referral_code = generate_referral_code()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.phone_number} ({self.user_type})"


# =========================================================
# DRIVER PROFILE
# =========================================================

class DriverProfile(models.Model):

    VEHICLE_CHOICES = [
        ("motorcycle", "Motorcycle"),
        ("car", "Car"),
        ("truck", "Truck"),
        ("van", "Van"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="driver_profile")

    vehicle_type = models.CharField(max_length=50, choices=VEHICLE_CHOICES, blank=True)

    vehicle_number = models.CharField(max_length=20, blank=True, null=True)

    license_number = models.CharField(max_length=50, blank=True, null=True)

    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=False)

    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# =========================================================
# OTP MODEL
# =========================================================

class PasswordResetOTP(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    otp_code = models.CharField(max_length=6)

    created_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField(null=True, blank=True)

    is_used = models.BooleanField(default=False)

    @property
    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at

    @classmethod
    def create_otp(cls, user, expiry_minutes=10):
        cls.objects.filter(user=user, is_used=False).delete()

        return cls.objects.create(
            user=user,
            otp_code=str(random.randint(100000, 999999)),
            expires_at=timezone.now() + timedelta(minutes=expiry_minutes)
        )


# =========================================================
# LOGIN ATTEMPTS
# =========================================================

class LoginAttempt(models.Model):

    identifier = models.CharField(max_length=255, db_index=True)

    failed_attempts = models.PositiveIntegerField(default=0)

    locked_until = models.DateTimeField(null=True, blank=True)

    @property
    def is_locked(self):
        return self.locked_until and self.locked_until > timezone.now()