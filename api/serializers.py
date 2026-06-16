from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, Station, FuelPrice, Order, Notification,
    Vehicle, VehicleCost, VehicleIssue, VehicleMeterHistory
)
from django.conf import settings
import re

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'email', 'full_name', 'user_type', 
                  'location', 'is_verified', 'created_at']

class RegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)
    user_type = serializers.CharField(default='customer')
    location = serializers.CharField(required=False, allow_blank=True)
    referral_code = serializers.CharField(required=False, allow_blank=True)
    vehicle_type = serializers.CharField(required=False, allow_blank=True)
    vehicle_number = serializers.CharField(required=False, allow_blank=True)
    license_number = serializers.CharField(required=False, allow_blank=True)
    
    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        
        password = data['password']
        if not re.search(r'[A-Z]', password):
            raise serializers.ValidationError({"password": "Password must contain at least one uppercase letter"})
        if not re.search(r'[a-z]', password):
            raise serializers.ValidationError({"password": "Password must contain at least one lowercase letter"})
        if not re.search(r'\d', password):
            raise serializers.ValidationError({"password": "Password must contain at least one number"})
        if not re.search(r'[\W_]', password):
            raise serializers.ValidationError({"password": "Password must contain at least one special character"})
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            phone_number=validated_data['phone_number'],
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            user_type=validated_data.get('user_type', 'customer'),
            location=validated_data.get('location', ''),
            referral_code=validated_data.get('referral_code', ''),
            vehicle_type=validated_data.get('vehicle_type'),
            vehicle_number=validated_data.get('vehicle_number'),
            license_number=validated_data.get('license_number'),
        )
        return user

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')
        
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                "error": "account_not_found",
                "message": "No account found with this phone number"
            })
        
        if user.is_locked():
            remaining = user.get_lockout_time_remaining()
            raise serializers.ValidationError({
                "error": "account_locked",
                "message": f"Too many failed attempts. Please try again in {remaining // 60} minutes",
                "lockout_seconds": remaining,
                "remaining_attempts": 0
            })
        
        user_auth = authenticate(phone_number=phone_number, password=password)
        
        if user_auth is None:
            remaining_attempts = user.increment_failed_attempts()
            remaining_attempts_left = settings.MAX_LOGIN_ATTEMPTS - user.failed_login_attempts
            
            error_data = {
                "error": "invalid_credentials",
                "message": f"Invalid credentials. {remaining_attempts_left} attempts remaining.",
                "remaining_attempts": remaining_attempts_left
            }
            
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                error_data["message"] = f"Account locked. Please try again in {settings.LOGIN_LOCKOUT_TIME_MINUTES} minutes."
                error_data["error"] = "account_locked"
            
            raise serializers.ValidationError(error_data)
        
        user_auth.reset_failed_attempts()
        data['user'] = user_auth
        return data

# =========================================================
# STATION SERIALIZERS
# =========================================================

class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ['id', 'name', 'location', 'address', 'latitude', 'longitude', 
                  'rating', 'reviews_count', 'image', 'is_open', 'is_24_7', 
                  'price_per_gallon', 'fuel_types']

class FuelPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelPrice
        fields = ['id', 'fuel_type', 'price', 'updated_at']

class StationDetailSerializer(serializers.ModelSerializer):
    prices = FuelPriceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Station
        fields = ['id', 'name', 'location', 'address', 'latitude', 'longitude', 
                  'rating', 'reviews_count', 'image', 'is_open', 'is_24_7', 
                  'price_per_gallon', 'fuel_types', 'prices']

# =========================================================
# VEHICLE SERIALIZERS
# =========================================================

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class VehicleCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleCost
        fields = '__all__'

class VehicleIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleIssue
        fields = '__all__'

class VehicleMeterHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleMeterHistory
        fields = '__all__'

class VehicleDetailSerializer(serializers.ModelSerializer):
    costs = VehicleCostSerializer(many=True, read_only=True)
    issues = VehicleIssueSerializer(many=True, read_only=True)
    meter_history = VehicleMeterHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Vehicle
        fields = '__all__'

# =========================================================
# ORDER SERIALIZERS
# =========================================================

class OrderSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_reference', 'station', 'station_name', 'fuel_type', 
                  'quantity', 'total_amount', 'delivery_location', 'status', 
                  'scheduled_delivery', 'created_at']

# =========================================================
# NOTIFICATION SERIALIZERS
# =========================================================

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'type', 'created_at']

# =========================================================
# DASHBOARD SERIALIZERS
# =========================================================

class DashboardDataSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    active_orders = serializers.IntegerField()
    recent_orders = OrderSerializer(many=True)
    recommended_stations = StationSerializer(many=True)
    notifications = NotificationSerializer(many=True)
    user = UserSerializer()

class VehicleDashboardDataSerializer(serializers.Serializer):
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    service_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    other_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    overdue_issues = serializers.IntegerField()
    open_issues = serializers.IntegerField()
    total_issues = serializers.IntegerField()
    meter_usage = serializers.ListField(child=serializers.IntegerField())
    vehicle = VehicleSerializer()