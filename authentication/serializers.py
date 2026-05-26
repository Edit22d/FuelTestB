import re
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()

# ──────────────────────────────────────────────────────────────
# Validation Regex Patterns (Match Flutter Frontend Exactly)
# ──────────────────────────────────────────────────────────────

# Phone: Must start with +, contain digits/spaces/dashes, min 11 chars total
# Examples: +256744692050, +256 744 692 050, +1-555-123-4567
PHONE_RE = re.compile(r'^\+[\d\s\-]{10,}$')

# Password: 8+ chars, uppercase, lowercase, digit, special character
# Matches Flutter: r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
PASS_RE = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$')

# Name: First + Last name (letters + single spaces only)
NAME_RE = re.compile(r"^[a-zA-Z]+(?: [a-zA-Z]+)+$")


def _normalize_phone(phone: str) -> str:
    """
    Remove spaces and dashes for consistent database comparison.
    Example: '+256 744 692 050' → '+256744692050'
    """
    return re.sub(r'[\s\-]', '', phone)


# ──────────────────────────────────────────────────────────────
# RegisterSerializer - Enhanced Security & Full Field Support
# ──────────────────────────────────────────────────────────────
class RegisterSerializer(serializers.Serializer):
    # ─── Required Fields ─────────────────────────────────────
    full_name = serializers.CharField(
        max_length=150,
        trim_whitespace=True,
        error_messages={
            'required': 'Full name is required.',
            'blank': 'Full name cannot be empty.',
            'max_length': 'Full name must be 150 characters or less.'
        }
    )
    email = serializers.EmailField(
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Enter a valid email address.',
            'blank': 'Email cannot be empty.'
        }
    )
    phone_number = serializers.CharField(
        max_length=20,
        trim_whitespace=True,
        error_messages={
            'required': 'Phone number is required.',
            'blank': 'Phone number cannot be empty.',
            'max_length': 'Phone number must be 20 characters or less.'
        }
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            'required': 'Password is required.',
            'blank': 'Password cannot be empty.',
            'min_length': 'Password must be at least 8 characters.'
        }
    )
    confirm_password = serializers.CharField(
        write_only=True,
        error_messages={
            'required': 'Please confirm your password.',
            'blank': 'Password confirmation cannot be empty.'
        }
    )
    
    # ─── Optional Fields with Defaults ───────────────────────
    user_type = serializers.ChoiceField(
        choices=['customer', 'driver'],
        default='customer',
        error_messages={
            'invalid_choice': 'User type must be either "customer" or "driver".'
        }
    )
    location = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True
    )
    referral_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True
    )

    # ─── Driver-Specific Fields (Validated Conditionally) ────
    vehicle_type = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True
    )
    vehicle_number = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True
    )
    license_number = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True
    )

    # ─── Field-Level Validators ──────────────────────────────
    
    def validate_full_name(self, value):
        """Validate full name format: First + Last name, letters only."""
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError('Full name must be at least 3 characters.')
        if not NAME_RE.match(value):
            raise serializers.ValidationError(
                'Enter a valid full name with first and last name (letters only, separated by space). Example: John Doe'
            )
        return value

    def validate_email(self, value):
        """Validate email format and check uniqueness (case-insensitive)."""
        value = value.lower().strip()
        # Case-insensitive uniqueness check using __iexact
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate_phone_number(self, value):
        """Validate phone format and check uniqueness (normalized comparison)."""
        value = value.strip()
        
        # Format validation: must start with + and have 11+ total chars
        if not PHONE_RE.match(value):
            raise serializers.ValidationError(
                'Phone must start with + and be at least 11 characters. Example: +256 744 692 050'
            )
        
        # Normalize for comparison (remove spaces/dashes)
        normalized = _normalize_phone(value)
        if len(normalized) < 11:
            raise serializers.ValidationError('Phone number must contain at least 11 digits including country code.')
        
        # Check uniqueness against existing users (normalized comparison)
        existing_users = User.objects.filter(
            phone_number__isnull=False
        ).exclude(phone_number__exact='')
        
        for user in existing_users:
            if user.phone_number and _normalize_phone(user.phone_number) == normalized:
                raise serializers.ValidationError('An account with this phone number already exists.')
        
        return value

    def validate_password(self, value):
        """Validate password strength: 8+ chars, uppercase, lowercase, digit, symbol."""
        if not PASS_RE.match(value):
            raise serializers.ValidationError(
                'Password must be at least 8 characters and include: uppercase letter, lowercase letter, number, and special character (!@#$%^&* etc.).'
            )
        return value

    # ─── Object-Level Validation ─────────────────────────────
    
    def validate(self, data):
        """Cross-field validation: password match + conditional driver fields."""
        
        # Password confirmation match
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        
        # Driver-specific field validation (only when user_type is 'driver')
        if data.get('user_type') == 'driver':
            required_driver_fields = {
                'vehicle_type': 'Vehicle type',
                'vehicle_number': 'Vehicle number',
                'license_number': 'License number'
            }
            errors = {}
            for field, label in required_driver_fields.items():
                value = data.get(field)
                if not value or (isinstance(value, str) and not value.strip()):
                    errors[field] = f'{label} is required for driver accounts.'
            if errors:
                raise serializers.ValidationError(errors)
        
        return data

    # ─── Create User Method ──────────────────────────────────
    
    def create(self, validated_data):
        """Create User instance and optional DriverProfile."""
        from authentication.models import DriverProfile
        
        # Remove non-User model fields from validated_data
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password')
        
        # Extract driver fields before creating user
        driver_fields = {
            'vehicle_type': validated_data.pop('vehicle_type', None),
            'vehicle_number': validated_data.pop('vehicle_number', None),
            'license_number': validated_data.pop('license_number', None),
        }
        
        # Normalize phone number before saving (store clean version)
        if 'phone_number' in validated_data and validated_data['phone_number']:
            validated_data['phone_number'] = validated_data['phone_number'].strip()
        
        # Create the User instance
        user = User(**validated_data)
        user.set_password(password)  # Hash password before saving
        user.save()
        
        # Create DriverProfile if applicable
        if user.user_type == 'driver' and driver_fields.get('vehicle_type'):
            DriverProfile.objects.create(
                user=user,
                vehicle_type=driver_fields['vehicle_type'].strip() if driver_fields['vehicle_type'] else '',
                vehicle_number=driver_fields['vehicle_number'].strip() if driver_fields.get('vehicle_number') else '',
                license_number=driver_fields['license_number'].strip() if driver_fields.get('license_number') else '',
            )
        
        return user


# ──────────────────────────────────────────────────────────────
# LoginSerializer - Accepts Email OR Phone (Matches Flutter)
# ──────────────────────────────────────────────────────────────
class LoginSerializer(serializers.Serializer):
    """
    Accepts email address OR phone number (with country code) + password.
    
    Phone format examples:
    - +256 744 692 050
    - +256744692050
    - +1-555-123-4567
    
    Email format: standard RFC-compliant email address
    """
    email_or_phone = serializers.CharField(
        required=True,
        trim_whitespace=True,
        error_messages={
            'required': 'Email or phone number is required.',
            'blank': 'Email or phone number cannot be empty.'
        }
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            'required': 'Password is required.',
            'blank': 'Password cannot be empty.'
        }
    )

    def validate_email_or_phone(self, value):
        """Validate format: phone (if starts with +) or email."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Email or phone number is required.')
        
        # If it looks like a phone number (starts with +), validate phone format
        if value.startswith('+'):
            if not PHONE_RE.match(value):
                raise serializers.ValidationError(
                    'Invalid phone format. Use: +256 744 692 050'
                )
        # Otherwise treat as email and validate email format
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
            raise serializers.ValidationError('Invalid email format.')
        
        return value


# ──────────────────────────────────────────────────────────────
# ForgotPasswordSerializer
# ──────────────────────────────────────────────────────────────
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Enter a valid email address.',
            'blank': 'Email cannot be empty.'
        }
    )
    
    def validate_email(self, value):
        """Normalize email to lowercase for consistent lookup."""
        return value.lower().strip()


# ──────────────────────────────────────────────────────────────
# ResetPasswordSerializer
# ──────────────────────────────────────────────────────────────
class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Enter a valid email address.'
        }
    )
    token = serializers.CharField(
        max_length=6,
        min_length=6,
        error_messages={
            'required': 'Reset code is required.',
            'min_length': 'Reset code must be 6 digits.',
            'max_length': 'Reset code must be 6 digits.',
            'blank': 'Reset code cannot be empty.'
        }
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            'required': 'New password is required.',
            'min_length': 'Password must be at least 8 characters.'
        }
    )
    confirm_new_password = serializers.CharField(
        write_only=True,
        error_messages={
            'required': 'Please confirm your new password.'
        }
    )

    def validate_new_password(self, value):
        """Validate new password strength (same rules as registration)."""
        if not PASS_RE.match(value):
            raise serializers.ValidationError(
                'Password must be at least 8 characters and include: uppercase, lowercase, number, and special character.'
            )
        return value

    def validate(self, data):
        """Ensure new password and confirmation match."""
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({
                'confirm_new_password': 'Passwords do not match.'
            })
        return data


# ──────────────────────────────────────────────────────────────
# UserSerializer - For API Responses (Read-Only)
# ──────────────────────────────────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    """
    Serializes User model for API responses.
    Includes driver_profile details conditionally.
    """
    driver_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'phone_number',
            'user_type',
            'location',
            'date_joined',
            'is_active',
            'driver_profile'
        ]
        read_only_fields = fields  # All fields are read-only for serialization

    def get_driver_profile(self, obj):
        """
        Include driver profile details only if:
        1. User type is 'driver'
        2. DriverProfile relation exists
        """
        if (
            obj.user_type == 'driver' and
            hasattr(obj, 'driver_profile') and
            obj.driver_profile
        ):
            dp = obj.driver_profile
            return {
                'vehicle_type': dp.vehicle_type,
                'vehicle_number': dp.vehicle_number,
                'license_number': dp.license_number,
                'is_verified': getattr(dp, 'is_verified', False),
                'verified_at': getattr(dp, 'verified_at', None),
            }
        return None