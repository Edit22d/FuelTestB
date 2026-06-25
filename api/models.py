# api/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import uuid

# =========================================================
# USER AUTHENTICATION MODELS
# =========================================================

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, email, full_name, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        user = self.model(
            phone_number=phone_number,
            email=email,
            full_name=full_name,
            **extra_fields
        )
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(phone_number, email, full_name, password, **extra_fields)

class User(AbstractUser):
    username = None
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    user_type = models.CharField(max_length=20, choices=[
        ('customer', 'Customer'),
        ('driver', 'Driver'),
        ('station_owner', 'Station Owner'),
        ('admin', 'Admin')
    ], default='customer')
    location = models.CharField(max_length=255, blank=True, null=True)
    referral_code = models.CharField(max_length=50, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(default=timezone.now)
    
    # Driver specific fields
    vehicle_type = models.CharField(max_length=100, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Login attempt tracking
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email', 'full_name']
    
    objects = CustomUserManager()
    
    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"
    
    def is_locked(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        if self.locked_until and self.locked_until <= timezone.now():
            self.failed_login_attempts = 0
            self.locked_until = None
            self.save(update_fields=['failed_login_attempts', 'locked_until'])
        return False
    
    def increment_failed_attempts(self):
        self.failed_login_attempts += 1
        
        if self.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            self.locked_until = timezone.now() + timedelta(minutes=settings.LOGIN_LOCKOUT_TIME_MINUTES)
        
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
        return self.failed_login_attempts
    
    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
    
    def get_remaining_attempts(self):
        if self.is_locked():
            return 0
        return max(0, settings.MAX_LOGIN_ATTEMPTS - self.failed_login_attempts)
    
    def get_lockout_time_remaining(self):
        if self.locked_until and self.locked_until > timezone.now():
            return int((self.locked_until - timezone.now()).total_seconds())
        return 0

class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.phone_number} - {'Success' if self.success else 'Failed'} - {self.timestamp}"

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()
    
    def __str__(self):
        return f"Reset token for {self.user.phone_number}"

# =========================================================
# STATION & FUEL MODELS
# =========================================================

class Station(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    reviews_count = models.IntegerField(default=0)
    image = models.CharField(max_length=500, blank=True, null=True)
    is_open = models.BooleanField(default=True)
    is_24_7 = models.BooleanField(default=False)
    price_per_gallon = models.DecimalField(max_digits=10, decimal_places=2, default=3.60)
    # fuel_types is a CharField - comma separated values
    fuel_types = models.CharField(max_length=255, default='Petrol,Diesel,Gas')
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
    ], default='active')
    operating_hours = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class FuelType(models.Model):
    FUEL_TYPES = [
        ('gas', 'Gas'),
        ('diesel', 'Diesel'),
        ('petrol', 'Petrol'),
        ('lpg', 'LPG'),
    ]
    
    name = models.CharField(max_length=50, choices=FUEL_TYPES, default='petrol')
    price_per_liter = models.DecimalField(max_digits=10, decimal_places=2)
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='fuel_type_entries')
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['station', 'name']
    
    def __str__(self):
        return f"{self.get_name_display()} - {self.station.name}"

class FuelPrice(models.Model):
    """Historical fuel price tracking"""
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='prices')
    fuel_type = models.CharField(max_length=50, choices=FuelType.FUEL_TYPES, default='petrol')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['station', 'fuel_type']
    
    def __str__(self):
        return f"{self.station.name} - {self.fuel_type}: {self.price}"

# =========================================================
# DELIVERY AGENT MODELS
# =========================================================

class DeliveryAgent(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_agent')
    phone = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=50)
    vehicle_plate = models.CharField(max_length=20)
    current_location = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_deliveries = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.vehicle_type}"

# =========================================================
# ORDER MODELS
# =========================================================

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='orders')
    fuel_type = models.ForeignKey(FuelType, on_delete=models.CASCADE, related_name='orders')
    delivery_agent = models.ForeignKey(DeliveryAgent, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.TextField()
    delivery_latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    delivery_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)
    delivery_notes = models.TextField(blank=True)
    order_reference = models.CharField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.order_reference:
            self.order_reference = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order {self.order_reference} - {self.user.full_name}"

# =========================================================
# PAYMENT MODELS
# =========================================================

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount}"

# =========================================================
# NOTIFICATION MODELS
# =========================================================

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order', 'Order Update'),
        ('payment', 'Payment Update'),
        ('delivery', 'Delivery Update'),
        ('promotion', 'Promotion'),
        ('system', 'System'),
        ('security', 'Security Alert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.full_name}"

# =========================================================
# SECURITY & LOGGING MODELS
# =========================================================

class SecurityLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_logs', null=True, blank=True)
    event_type = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at}"

# =========================================================
# DASHBOARD STATS MODELS
# =========================================================

class DashboardStats(models.Model):
    date = models.DateField(auto_now_add=True)
    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    active_stations = models.IntegerField(default=0)
    active_agents = models.IntegerField(default=0)
    pending_orders = models.IntegerField(default=0)
    completed_orders = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Stats for {self.date}"

# =========================================================
# VEHICLE MANAGEMENT MODELS (Fleet Management)
# =========================================================

class Vehicle(models.Model):
    """Vehicle model for fleet management"""
    FUEL_TYPES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('lpg', 'LPG'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_service', 'Out of Service'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=255)
    year = models.IntegerField()
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    trim = models.CharField(max_length=100, blank=True, null=True)
    vin = models.CharField(max_length=50, unique=True)
    license_plate = models.CharField(max_length=50, blank=True, null=True)
    
    # Vehicle Details
    fuel_type = models.CharField(max_length=50, choices=FUEL_TYPES, default='petrol')
    meter_reading = models.IntegerField(default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    
    # Type and Group
    vehicle_type = models.CharField(max_length=100, default='Trailer')
    group = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    
    # Driver Assignment
    driver_name = models.CharField(max_length=255, blank=True, null=True)
    driver_phone = models.CharField(max_length=50, blank=True, null=True)
    driver_email = models.EmailField(blank=True, null=True)
    driver_address = models.TextField(blank=True, null=True)
    
    # Operational
    operator = models.CharField(max_length=255, default='Unassigned')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.vin}"

class VehicleCost(models.Model):
    """Cost of ownership for vehicles"""
    COST_TYPES = [
        ('total', 'Total Costs'),
        ('service', 'Service Costs'),
        ('other', 'Other Costs'),
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='costs')
    cost_type = models.CharField(max_length=50, choices=COST_TYPES, default='total')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.vehicle.name} - {self.cost_type}: {self.amount}"

class VehicleIssue(models.Model):
    """Issues and maintenance for vehicles"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='issues')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_overdue = models.BooleanField(default=False)
    is_open = models.BooleanField(default=True)
    priority = models.CharField(max_length=50, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.vehicle.name} - {self.title}"

class VehicleMeterHistory(models.Model):
    """Meter/odometer history tracking"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='meter_history')
    reading = models.IntegerField()
    date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.vehicle.name} - {self.reading} mi"

class VehicleAssignment(models.Model):
    """Vehicle assignment history"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.CharField(max_length=255)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='vehicle_assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    returned_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.vehicle.name} assigned to {self.assigned_to}"