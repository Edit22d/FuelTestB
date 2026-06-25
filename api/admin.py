from django.contrib import admin
from .models import (
    User, LoginHistory, PasswordResetToken, 
    Station, FuelType, FuelPrice, 
    Vehicle, VehicleCost, VehicleIssue, VehicleMeterHistory, VehicleAssignment,
    Order, Notification, DeliveryAgent, Payment, SecurityLog, DashboardStats
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
    list_display = ['name', 'address', 'phone', 'email', 'rating', 'status', 'is_open']
    search_fields = ['name', 'address', 'phone', 'email']
    list_filter = ['status', 'is_open']
    ordering = ['-rating']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'phone', 'email', 'image')
        }),
        ('Location (GPS)', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Rating & Reviews', {
            'fields': ('rating', 'reviews_count')
        }),
        ('Operations', {
            'fields': ('status', 'is_open', 'is_24_7', 'price_per_gallon', 'operating_hours')
        }),
    )

@admin.register(FuelType)
class FuelTypeAdmin(admin.ModelAdmin):
    list_display = ['station', 'name', 'price_per_liter', 'available']
    list_filter = ['available', 'name']
    search_fields = ['station__name']

@admin.register(FuelPrice)
class FuelPriceAdmin(admin.ModelAdmin):
    list_display = ['station', 'fuel_type', 'price', 'updated_at']
    list_filter = ['fuel_type']
    search_fields = ['station__name']
    readonly_fields = ['updated_at']

# =========================================================
# DELIVERY AGENT MANAGEMENT
# =========================================================

@admin.register(DeliveryAgent)
class DeliveryAgentAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'vehicle_type', 'vehicle_plate', 'status', 'rating', 'total_deliveries']
    list_filter = ['status', 'vehicle_type']
    search_fields = ['user__full_name', 'user__phone_number', 'vehicle_plate']
    readonly_fields = ['total_deliveries', 'created_at', 'updated_at']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'order', 'amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['transaction_id', 'user__full_name', 'order__order_reference']
    readonly_fields = ['created_at', 'updated_at']

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
    list_display = ['vehicle', 'cost_type', 'amount', 'description', 'date']
    list_filter = ['cost_type']
    search_fields = ['vehicle__name', 'description']
    readonly_fields = ['date', 'created_at']

@admin.register(VehicleIssue)
class VehicleIssueAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'title', 'is_overdue', 'is_open', 'priority', 'created_at']
    list_filter = ['is_overdue', 'is_open', 'priority']
    search_fields = ['vehicle__name', 'title']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(VehicleMeterHistory)
class VehicleMeterHistoryAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'reading', 'date']
    list_filter = ['date']
    search_fields = ['vehicle__name']
    readonly_fields = ['date']

@admin.register(VehicleAssignment)
class VehicleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'assigned_to', 'assigned_date', 'is_active']
    list_filter = ['is_active']
    search_fields = ['vehicle__name', 'assigned_to']
    readonly_fields = ['assigned_date']

# =========================================================
# ORDER MANAGEMENT
# =========================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_reference', 'user', 'station', 'status', 'total_price', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_reference', 'user__full_name', 'user__phone_number']
    readonly_fields = ['order_reference', 'created_at', 'updated_at', 'delivered_at']
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

# =========================================================
# SECURITY & DASHBOARD
# =========================================================

@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'user', 'ip_address', 'location', 'created_at']
    list_filter = ['event_type']
    search_fields = ['user__full_name', 'ip_address']
    readonly_fields = ['created_at']

@admin.register(DashboardStats)
class DashboardStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_orders', 'total_revenue', 'active_stations', 'active_agents']
    readonly_fields = ['date']