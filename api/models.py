from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

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
# DASHBOARD MODELS
# =========================================================

class Station(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    reviews_count = models.IntegerField(default=0)
    image = models.CharField(max_length=500, blank=True, null=True)
    is_open = models.BooleanField(default=True)
    is_24_7 = models.BooleanField(default=False)
    price_per_gallon = models.DecimalField(max_digits=10, decimal_places=2, default=3.60)
    fuel_types = models.CharField(max_length=255, default='Petrol,Diesel,Gas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-rating']
    
    def __str__(self):
        return self.name

class FuelPrice(models.Model):
    FUEL_TYPES = [
        ('gas', 'Gas'),
        ('diesel', 'Diesel'),
        ('petrol', 'Petrol'),
        ('lpg', 'LPG'),
    ]
    
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='prices')
    fuel_type = models.CharField(max_length=50, choices=FUEL_TYPES, default='petrol')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['station', 'fuel_type']
    
    def __str__(self):
        return f"{self.station.name} - {self.fuel_type}: {self.price}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    fuel_type = models.CharField(max_length=50)
    quantity = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_location = models.TextField()
    delivery_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    delivery_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    scheduled_delivery = models.DateTimeField(null=True, blank=True)
    order_reference = models.CharField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.order_reference:
            import uuid
            self.order_reference = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.order_reference} - {self.user.full_name}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order', 'Order'),
        ('promotion', 'Promotion'),
        ('system', 'System'),
        ('alert', 'Alert'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='system')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.full_name}"


# Add these models after your existing models

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
    name = models.CharField(max_length=255)  # e.g., "2020 Ford F-150"
    year = models.IntegerField()
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    trim = models.CharField(max_length=100, blank=True, null=True)
    vin = models.CharField(max_length=50, unique=True)
    license_plate = models.CharField(max_length=50, blank=True, null=True)
    
    # Vehicle Details
    fuel_type = models.CharField(max_length=50, choices=FUEL_TYPES, default='petrol')
    meter_reading = models.IntegerField(default=0)  # Miles/KM
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    
    # Type and Group
    vehicle_type = models.CharField(max_length=100, default='Trailer')  # Trailer, Truck, Van, etc.
    group = models.CharField(max_length=255, blank=True, null=True)  # Sales, Operations, etc.
    region = models.CharField(max_length=255, blank=True, null=True)  # USA / Southeast Region / Atlanta
    
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