# api/dashboard_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import json

from .models import (
    Station, FuelType, FuelPrice, DeliveryAgent,
    Order, Payment, Notification, SecurityLog, DashboardStats,
    Vehicle, VehicleCost, VehicleIssue, VehicleMeterHistory, VehicleAssignment,
    User
)
from .serializers import (
    StationSerializer, VehicleSerializer, OrderSerializer,
    PaymentSerializer, NotificationSerializer
)


# =========================================================
# CUSTOM DASHBOARD LOGIN & LOGOUT
# =========================================================

def dashboard_login(request):
    """Custom dashboard login page"""
    if request.user.is_authenticated:
        return redirect('dashboard_index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard_index')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    
    return render(request, 'dashboard/login.html')

def dashboard_logout(request):
    """Custom dashboard logout"""
    logout(request)
    return redirect('dashboard_login')


# =========================================================
# DASHBOARD INDEX VIEW
# =========================================================

@login_required(login_url='dashboard_login')
def dashboard_index(request):
    """Dashboard home page"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Stats
    total_stations = Station.objects.count()
    active_stations = Station.objects.filter(is_open=True).count()
    total_vehicles = Vehicle.objects.count()
    active_vehicles = Vehicle.objects.filter(status='active').count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    total_users = User.objects.count()
    unread_notifications = Notification.objects.filter(is_read=False).count()
    
    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:5]
    
    # Recent activities
    recent_activities = []
    for order in recent_orders:
        recent_activities.append({
            'title': f'New Order #{order.order_reference}',
            'desc': f'{order.user.full_name} ordered {order.quantity}L',
            'time': order.created_at,
            'icon': 'fa-shopping-cart'
        })
    
    context = {
        'total_stations': total_stations,
        'active_stations': active_stations,
        'total_vehicles': total_vehicles,
        'active_vehicles': active_vehicles,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'total_users': total_users,
        'unread_notifications': unread_notifications,
        'recent_orders': recent_orders,
        'recent_activities': recent_activities,
        'station_count': total_stations,
        'agent_count': DeliveryAgent.objects.count(),
        'pending_orders_count': pending_orders,
        'user': request.user,
    }
    
    return render(request, 'dashboard/index.html', context)


# =========================================================
# STATION CRUD VIEWS
# =========================================================

@login_required(login_url='dashboard_login')
def station_list(request):
    """List all stations"""
    stations = Station.objects.all().order_by('-created_at')
    
    # Search filter
    search = request.GET.get('search')
    if search:
        stations = stations.filter(
            Q(name__icontains=search) |
            Q(address__icontains=search)
        )
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'open':
            stations = stations.filter(is_open=True)
        elif status_filter == 'closed':
            stations = stations.filter(is_open=False)
    
    context = {
        'stations': stations,
        'station_count': stations.count(),
        'user': request.user,
    }
    return render(request, 'dashboard/stations/list.html', context)

@login_required(login_url='dashboard_login')
def station_create(request):
    """Create a new station with image upload"""
    if request.method == 'POST':
        try:
            # Handle image upload
            image_file = request.FILES.get('image')
            image_path = ''
            
            if image_file:
                # Ensure the stations directory exists
                stations_dir = os.path.join('media', 'stations')
                if not os.path.exists(stations_dir):
                    os.makedirs(stations_dir)
                
                # Save the image
                file_name = f'stations/{image_file.name}'
                saved_path = default_storage.save(file_name, ContentFile(image_file.read()))
                image_path = saved_path
            
            # Create the station - exclude fuel_types from initial creation
            station = Station(
                name=request.POST.get('name'),
                address=request.POST.get('address'),
                phone=request.POST.get('phone'),
                email=request.POST.get('email'),
                latitude=request.POST.get('latitude') or None,
                longitude=request.POST.get('longitude') or None,
                rating=request.POST.get('rating', 4.0),
                reviews_count=request.POST.get('reviews_count', 0),
                is_open=request.POST.get('is_open') == 'on',
                is_24_7=request.POST.get('is_24_7') == 'on',
                price_per_gallon=request.POST.get('price_per_gallon', 3.60),
                image=image_path,
            )
            station.save()
            
            # Handle fuel_types separately - it's a CharField
            fuel_types_value = request.POST.get('fuel_types', 'Petrol,Diesel,Gas')
            Station.objects.filter(id=station.id).update(fuel_types=fuel_types_value)
            
            messages.success(request, f'Station "{station.name}" created successfully!')
            return redirect('station_list')
            
        except Exception as e:
            messages.error(request, f'Error creating station: {str(e)}')
            print(f"Error creating station: {e}")
            import traceback
            traceback.print_exc()
    
    return render(request, 'dashboard/stations/create.html', {'user': request.user})

@login_required(login_url='dashboard_login')
def station_detail(request, pk):
    """View station details"""
    station = get_object_or_404(Station, pk=pk)
    
    # Get related data
    fuel_types = FuelType.objects.filter(station=station)
    orders = Order.objects.filter(station=station)[:10]
    
    context = {
        'station': station,
        'fuel_types': fuel_types,
        'orders': orders,
        'user': request.user,
    }
    return render(request, 'dashboard/stations/detail.html', context)

@login_required(login_url='dashboard_login')
def station_edit(request, pk):
    """Edit a station with image upload"""
    station = get_object_or_404(Station, pk=pk)
    
    if request.method == 'POST':
        try:
            # Handle image upload
            image_file = request.FILES.get('image')
            image_path = station.image
            
            if image_file:
                # Delete old image if exists
                if station.image and default_storage.exists(station.image):
                    default_storage.delete(station.image)
                
                # Ensure the stations directory exists
                stations_dir = os.path.join('media', 'stations')
                if not os.path.exists(stations_dir):
                    os.makedirs(stations_dir)
                
                # Save new image
                file_name = f'stations/{image_file.name}'
                saved_path = default_storage.save(file_name, ContentFile(image_file.read()))
                image_path = saved_path
            
            # Update station fields
            station.name = request.POST.get('name')
            station.address = request.POST.get('address')
            station.phone = request.POST.get('phone')
            station.email = request.POST.get('email')
            station.latitude = request.POST.get('latitude') or None
            station.longitude = request.POST.get('longitude') or None
            station.rating = request.POST.get('rating', 4.0)
            station.reviews_count = request.POST.get('reviews_count', 0)
            station.is_open = request.POST.get('is_open') == 'on'
            station.is_24_7 = request.POST.get('is_24_7') == 'on'
            station.price_per_gallon = request.POST.get('price_per_gallon', 3.60)
            station.image = image_path
            station.save()
            
            # Handle fuel_types separately - it's a CharField
            fuel_types_value = request.POST.get('fuel_types', 'Petrol,Diesel,Gas')
            Station.objects.filter(id=station.id).update(fuel_types=fuel_types_value)
            
            messages.success(request, f'Station "{station.name}" updated successfully!')
            return redirect('station_detail', pk=station.pk)
            
        except Exception as e:
            messages.error(request, f'Error updating station: {str(e)}')
            print(f"Error updating station: {e}")
            import traceback
            traceback.print_exc()
    
    context = {
        'station': station,
        'user': request.user,
    }
    return render(request, 'dashboard/stations/edit.html', context)

@login_required(login_url='dashboard_login')
def station_delete(request, pk):
    """Delete a station"""
    station = get_object_or_404(Station, pk=pk)
    
    if request.method == 'POST':
        # Delete associated image if exists
        if station.image and default_storage.exists(station.image):
            default_storage.delete(station.image)
        
        station_name = station.name
        station.delete()
        messages.success(request, f'Station "{station_name}" deleted successfully!')
        return redirect('station_list')
    
    context = {
        'station': station,
        'user': request.user,
    }
    return render(request, 'dashboard/stations/delete.html', context)


# =========================================================
# VEHICLE VIEWS
# =========================================================

@login_required(login_url='dashboard_login')
def vehicle_list(request):
    """List all vehicles"""
    vehicles = Vehicle.objects.all()
    context = {'vehicles': vehicles, 'user': request.user}
    return render(request, 'dashboard/vehicles/list.html', context)

@login_required(login_url='dashboard_login')
def vehicle_create(request):
    """Create a new vehicle"""
    if request.method == 'POST':
        vehicle = Vehicle(
            name=request.POST.get('name'),
            year=request.POST.get('year'),
            make=request.POST.get('make'),
            model=request.POST.get('model'),
            trim=request.POST.get('trim'),
            vin=request.POST.get('vin'),
            license_plate=request.POST.get('license_plate'),
            fuel_type=request.POST.get('fuel_type'),
            meter_reading=request.POST.get('meter_reading', 0),
            status=request.POST.get('status'),
            vehicle_type=request.POST.get('vehicle_type'),
            group=request.POST.get('group'),
            region=request.POST.get('region'),
            driver_name=request.POST.get('driver_name'),
            driver_phone=request.POST.get('driver_phone'),
            driver_email=request.POST.get('driver_email'),
            driver_address=request.POST.get('driver_address'),
            operator=request.POST.get('operator', 'Unassigned'),
        )
        vehicle.save()
        messages.success(request, 'Vehicle created successfully!')
        return redirect('vehicle_list')
    
    return render(request, 'dashboard/vehicles/create.html', {'user': request.user})

@login_required(login_url='dashboard_login')
def vehicle_edit(request, pk):
    """Edit a vehicle"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        vehicle.name = request.POST.get('name')
        vehicle.year = request.POST.get('year')
        vehicle.make = request.POST.get('make')
        vehicle.model = request.POST.get('model')
        vehicle.trim = request.POST.get('trim')
        vehicle.vin = request.POST.get('vin')
        vehicle.license_plate = request.POST.get('license_plate')
        vehicle.fuel_type = request.POST.get('fuel_type')
        vehicle.meter_reading = request.POST.get('meter_reading', 0)
        vehicle.status = request.POST.get('status')
        vehicle.vehicle_type = request.POST.get('vehicle_type')
        vehicle.group = request.POST.get('group')
        vehicle.region = request.POST.get('region')
        vehicle.driver_name = request.POST.get('driver_name')
        vehicle.driver_phone = request.POST.get('driver_phone')
        vehicle.driver_email = request.POST.get('driver_email')
        vehicle.driver_address = request.POST.get('driver_address')
        vehicle.operator = request.POST.get('operator')
        vehicle.save()
        
        messages.success(request, 'Vehicle updated successfully!')
        return redirect('vehicle_list')
    
    context = {'vehicle': vehicle, 'user': request.user}
    return render(request, 'dashboard/vehicles/edit.html', context)

@login_required(login_url='dashboard_login')
def vehicle_detail(request, pk):
    """View vehicle details"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    context = {'vehicle': vehicle, 'user': request.user}
    return render(request, 'dashboard/vehicles/detail.html', context)

@login_required(login_url='dashboard_login')
def vehicle_delete(request, pk):
    """Delete a vehicle"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Vehicle deleted successfully!')
        return redirect('vehicle_list')
    return render(request, 'dashboard/vehicles/delete.html', {'vehicle': vehicle, 'user': request.user})


# =========================================================
# ORDER VIEWS
# =========================================================

@login_required(login_url='dashboard_login')
def order_list(request):
    """List all orders"""
    orders = Order.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    context = {'orders': orders, 'user': request.user}
    return render(request, 'dashboard/orders/list.html', context)

@login_required(login_url='dashboard_login')
def order_detail(request, pk):
    """View order details"""
    order = get_object_or_404(Order, pk=pk)
    context = {'order': order, 'user': request.user}
    return render(request, 'dashboard/orders/detail.html', context)


# =========================================================
# PAYMENT VIEWS
# =========================================================

@login_required(login_url='dashboard_login')
def payment_list(request):
    """List all payments"""
    payments = Payment.objects.all().order_by('-created_at')
    context = {'payments': payments, 'user': request.user}
    return render(request, 'dashboard/payments/list.html', context)

@login_required(login_url='dashboard_login')
def payment_detail(request, pk):
    """View payment details"""
    payment = get_object_or_404(Payment, pk=pk)
    context = {'payment': payment, 'user': request.user}
    return render(request, 'dashboard/payments/detail.html', context)


# =========================================================
# NOTIFICATION VIEWS
# =========================================================

@login_required(login_url='dashboard_login')
def notification_list(request):
    """List all notifications"""
    notifications = Notification.objects.all().order_by('-created_at')
    context = {'notifications': notifications, 'user': request.user}
    return render(request, 'dashboard/notifications/list.html', context)

@login_required(login_url='dashboard_login')
def notification_create(request):
    """Create a new notification"""
    if request.method == 'POST':
        notification = Notification(
            user_id=request.POST.get('user'),
            title=request.POST.get('title'),
            message=request.POST.get('message'),
            type=request.POST.get('type'),
        )
        notification.save()
        messages.success(request, 'Notification created successfully!')
        return redirect('notification_list')
    
    users = User.objects.all()
    context = {'users': users, 'user': request.user}
    return render(request, 'dashboard/notifications/create.html', context)


# =========================================================
# SECURITY VIEWS
# =========================================================

@login_required(login_url='dashboard_login')
def security_logs(request):
    """View security logs"""
    logs = SecurityLog.objects.all().order_by('-created_at')
    context = {'logs': logs, 'user': request.user}
    return render(request, 'dashboard/security/logs.html', context)


# =========================================================
# USER MANAGEMENT VIEWS (Dashboard)
# =========================================================

@login_required(login_url='dashboard_login')
def user_list(request):
    """List all users in dashboard"""
    users = User.objects.all().order_by('-date_joined')
    context = {'users': users, 'user': request.user}
    return render(request, 'dashboard/users/list.html', context)

@login_required(login_url='dashboard_login')
def user_detail(request, user_id):
    """View user details in dashboard"""
    user_obj = get_object_or_404(User, id=user_id)
    context = {'user_obj': user_obj, 'user': request.user}
    return render(request, 'dashboard/users/detail.html', context)