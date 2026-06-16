from django.contrib import admin
from .models import (
    User, LoginHistory, PasswordResetToken, 
    Station, FuelPrice, 
    Vehicle, VehicleCost, VehicleIssue, VehicleMeterHistory,
    Order, Notification
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'email', 'full_name', 'user_type', 'is_active', 'failed_login_attempts']
    search_fields = ['phone_number', 'email', 'full_name']
    list_filter = ['user_type', 'is_active', 'is_verified']
    readonly_fields = ['created_at', 'updated_at', 'last_activity']

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'success', 'timestamp', 'ip_address']
    list_filter = ['success']
    search_fields = ['user__phone_number']
    readonly_fields = ['timestamp']

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at', 'used']
    list_filter = ['used']
    search_fields = ['user__phone_number']
    readonly_fields = ['created_at']

# =========================================================
# STATION MANAGEMENT
# =========================================================

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'rating', 'is_open', 'is_24_7', 'price_per_gallon']
    search_fields = ['name', 'location', 'address']
    list_filter = ['is_open', 'is_24_7']
    ordering = ['-rating']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'address', 'image')
        }),
        ('Location (GPS)', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Rating & Reviews', {
            'fields': ('rating', 'reviews_count')
        }),
        ('Operations', {
            'fields': ('is_open', 'is_24_7', 'price_per_gallon', 'fuel_types')
        }),
    )

@admin.register(FuelPrice)
class FuelPriceAdmin(admin.ModelAdmin):
    list_display = ['station', 'fuel_type', 'price', 'updated_at']
    list_filter = ['fuel_type']
    search_fields = ['station__name']
    readonly_fields = ['updated_at']

# =========================================================
# VEHICLE MANAGEMENT
# =========================================================

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['name', 'vin', 'license_plate', 'status', 'driver_name', 'is_active']
    search_fields = ['name', 'vin', 'license_plate', 'driver_name']
    list_filter = ['status', 'fuel_type', 'is_active', 'year']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'year', 'make', 'model', 'trim')
        }),
        ('Identification', {
            'fields': ('vin', 'license_plate')
        }),
        ('Vehicle Details', {
            'fields': ('fuel_type', 'meter_reading', 'status', 'vehicle_type')
        }),
        ('Assignment', {
            'fields': ('group', 'region', 'operator')
        }),
        ('Driver Details', {
            'fields': ('driver_name', 'driver_phone', 'driver_email', 'driver_address'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

@admin.register(VehicleCost)
class VehicleCostAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'cost_type', 'amount', 'date']
    list_filter = ['cost_type']
    search_fields = ['vehicle__name']
    readonly_fields = ['date', 'created_at']

@admin.register(VehicleIssue)
class VehicleIssueAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'title', 'is_overdue', 'is_open', 'priority']
    list_filter = ['is_overdue', 'is_open', 'priority']
    search_fields = ['vehicle__name', 'title']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(VehicleMeterHistory)
class VehicleMeterHistoryAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'reading', 'date']
    list_filter = ['date']
    search_fields = ['vehicle__name']
    readonly_fields = ['date']

# =========================================================
# ORDER MANAGEMENT
# =========================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_reference', 'user', 'station', 'fuel_type', 'quantity', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_reference', 'user__full_name', 'user__phone_number']
    readonly_fields = ['order_reference', 'created_at', 'updated_at']
    ordering = ['-created_at']

# =========================================================
# NOTIFICATION MANAGEMENT
# =========================================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_read', 'type', 'created_at']
    list_filter = ['is_read', 'type', 'created_at']
    search_fields = ['user__full_name', 'title']
    readonly_fields = ['created_at']
    ordering = ['-created_at']