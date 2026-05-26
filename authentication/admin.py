from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, DriverProfile, PasswordResetOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'phone_number', 'user_type', 'is_active', 'date_joined']
    list_filter  = ['user_type', 'is_active', 'is_staff']
    search_fields = ['email', 'full_name', 'phone_number']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone_number', 'location', 'referral_code')}),
        ('Account', {'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone_number', 'user_type', 'password1', 'password2'),
        }),
    )


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'vehicle_type', 'vehicle_number', 'license_number', 'is_verified']
    list_filter  = ['is_verified', 'vehicle_type']
    search_fields = ['user__email', 'vehicle_number', 'license_number']


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp_code', 'created_at', 'is_used']
    list_filter  = ['is_used']
    search_fields = ['user__email']
    readonly_fields = ['created_at']
