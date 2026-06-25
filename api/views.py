# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes 
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.db import models
import uuid
import requests
import random
import traceback

from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    StationSerializer, StationDetailSerializer, FuelPriceSerializer,
    OrderSerializer, NotificationSerializer, DashboardDataSerializer,
    VehicleSerializer, VehicleDetailSerializer, VehicleCostSerializer,
    VehicleIssueSerializer, PaymentSerializer
)
from .models import (
    User, LoginHistory, PasswordResetToken, Station, FuelPrice,
    Order, Notification, Vehicle, VehicleCost, VehicleIssue,
    VehicleMeterHistory, DeliveryAgent, Payment, SecurityLog,
    DashboardStats, FuelType
)

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def send_reset_email(user_email, reset_token):
    """Send password reset email with OTP"""
    subject = '🔐 Password Reset Request - Fuel Connect'
    
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background-color: #f6f9fc;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: #ffffff;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.08);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #C4963D, #D4A84D);
                padding: 30px 40px;
                text-align: center;
            }}
            .header h1 {{
                color: #ffffff;
                font-size: 24px;
                font-weight: 700;
                margin: 0;
            }}
            .content {{
                padding: 40px;
            }}
            .token-box {{
                background: #f7fafc;
                border: 2px dashed #C4963D;
                border-radius: 16px;
                padding: 24px;
                text-align: center;
                margin: 24px 0;
            }}
            .token-box .token {{
                font-family: 'Courier New', monospace;
                font-size: 32px;
                font-weight: 700;
                color: #1a2a3a;
                letter-spacing: 4px;
                display: block;
                background: #ffffff;
                border-radius: 8px;
                padding: 12px 0;
            }}
            .footer {{
                background: #f7fafc;
                padding: 24px 40px;
                text-align: center;
            }}
            .footer p {{
                color: #a0aec0;
                font-size: 12px;
                margin: 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⛽ Fuel Connect</h1>
                <p>Secure Password Reset</p>
            </div>
            <div class="content">
                <h2>🔐 Reset Your Password</h2>
                <p>Hello,</p>
                <p>We received a request to reset the password for your Fuel Connect account.</p>
                <div class="token-box">
                    <div class="label">🔑 Verification Code</div>
                    <span class="token">{reset_token}</span>
                </div>
                <p>This code will expire in <strong>5 minutes</strong>.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </div>
            <div class="footer">
                <p><strong>Fuel Connect</strong> — Smart Fuel Tracking</p>
                <p>&copy; 2026 Fuel Connect. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    '''.replace('{reset_token}', reset_token)
    
    plain_message = f'''
Hello,

You requested to reset your password for your Fuel Connect account.

Your 6-digit verification code is: {reset_token}

Please enter this code in the app to reset your password.

This code will expire in 5 minutes.

If you did not request this, please ignore this email.

Best regards,
Fuel Connect Team
'''
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
            html_message=html_message,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

# =========================================================
# AUTHENTICATION VIEWS
# =========================================================

class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        captcha_token = request.data.get('captcha_token')
        
        if not captcha_token:
            return Response({
                'success': False,
                'message': 'Please complete the security verification',
                'requires_captcha': True,
                'error': 'captcha_required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not captcha_token.startswith('math_captcha_'):
            return Response({
                'success': False,
                'message': 'Invalid verification. Please try again.',
                'error': 'captcha_failed',
                'requires_captcha': True
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.last_activity = timezone.now()
            user.save(update_fields=['last_activity'])
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Account created successfully!',
                'data': {
                    'user': UserSerializer(user).data,
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Registration failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        captcha_token = request.data.get('captcha_token')
        phone_number = request.data.get('phone_number')
        
        try:
            user = User.objects.get(phone_number=phone_number)
            needs_captcha = False
            
            if user.last_activity:
                days_inactive = (timezone.now() - user.last_activity).days
                if days_inactive >= 14:
                    needs_captcha = True
            else:
                needs_captcha = True
            
            if needs_captcha and not captcha_token:
                return Response({
                    'success': False,
                    'message': 'Security verification required.',
                    'requires_captcha': True,
                    'error': 'captcha_required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if captcha_token and needs_captcha:
                if not captcha_token.startswith('math_captcha_'):
                    return Response({
                        'success': False,
                        'message': 'Invalid verification.',
                        'error': 'captcha_failed',
                        'requires_captcha': True
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
        except User.DoesNotExist:
            pass
        
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.last_activity = timezone.now()
            user.save(update_fields=['last_activity'])
            
            LoginHistory.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=True
            )
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Login successful',
                'data': {
                    'user': UserSerializer(user).data,
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                }
            }, status=status.HTTP_200_OK)
        
        phone_number = request.data.get('phone_number')
        if phone_number:
            try:
                user = User.objects.get(phone_number=phone_number)
                LoginHistory.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    success=False
                )
            except User.DoesNotExist:
                pass
        
        try:
            user = User.objects.get(phone_number=phone_number)
            if user.is_locked():
                remaining = user.get_lockout_time_remaining()
                minutes = remaining // 60
                return Response({
                    'success': False,
                    'message': f'Account locked. Try again in {minutes} minutes.',
                    'error': 'account_locked',
                    'lockout_seconds': remaining
                }, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            pass
        
        return Response({
            'success': False,
            'message': 'Invalid phone number or password',
            'error': 'invalid_credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

class SocialLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        provider = request.data.get('provider')
        access_token = request.data.get('access_token')
        id_token = request.data.get('id_token')
        
        token = id_token or access_token
        
        if not provider or not token:
            return Response({
                'success': False,
                'message': 'Provider and token are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = None
            
            if provider == 'google':
                google_data = None
                
                if id_token:
                    try:
                        google_url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={id_token}"
                        response = requests.get(google_url, timeout=10)
                        if response.status_code == 200:
                            google_data = response.json()
                    except Exception as e:
                        print(f"id_token verification failed: {e}")
                
                if not google_data and access_token:
                    try:
                        google_url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}"
                        response = requests.get(google_url, timeout=10)
                        if response.status_code == 200:
                            google_data = response.json()
                    except Exception as e:
                        print(f"access_token verification failed: {e}")
                
                if google_data and google_data.get('email'):
                    email = google_data.get('email')
                    full_name = google_data.get('name', email.split('@')[0])
                    
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            'full_name': full_name,
                            'phone_number': f"google_{uuid.uuid4().hex[:10]}",
                            'user_type': 'customer',
                            'is_verified': True,
                        }
                    )
                    
                    if created:
                        user.last_activity = timezone.now()
                        user.save()
                else:
                    return Response({
                        'success': False,
                        'message': 'Invalid Google token'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            elif provider == 'apple':
                email = request.data.get('email')
                full_name = request.data.get('full_name', 'Apple User')
                
                if email:
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            'full_name': full_name,
                            'phone_number': f"apple_{uuid.uuid4().hex[:10]}",
                            'user_type': 'customer',
                            'is_verified': True,
                        }
                    )
                    
                    if created:
                        user.last_activity = timezone.now()
                        user.save()
            
            if user:
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'success': True,
                    'message': f'{provider.title()} login successful',
                    'data': {
                        'user': UserSerializer(user).data,
                        'access_token': str(refresh.access_token),
                        'refresh_token': str(refresh),
                    }
                }, status=status.HTTP_200_OK)
            
            return Response({
                'success': False,
                'message': 'Social authentication failed'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            print(f"❌ Social login error: {str(e)}")
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'Authentication error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({
                'success': False,
                'message': 'Email or phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = None
            if '@' in phone_number:
                user = User.objects.filter(email=phone_number).first()
            else:
                user = User.objects.filter(phone_number=phone_number).first()
            
            if user:
                reset_token = ''.join(str(random.randint(0, 9)) for _ in range(6))
                email_sent = send_reset_email(user.email, reset_token)
                
                if email_sent:
                    return Response({
                        'success': True,
                        'message': 'A 6-digit verification code has been sent to your email'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': True,
                        'message': 'Verification code generated (check console for token)',
                        'reset_token': reset_token
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'No account found with this email or phone number'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        phone_number = request.data.get('phone_number')
        
        if not token or not new_password or not confirm_password or not phone_number:
            return Response({
                'success': False,
                'message': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({
                'success': False,
                'message': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(token) != 6 or not token.isdigit():
            return Response({
                'success': False,
                'message': 'Invalid or expired token.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = None
            if '@' in phone_number:
                user = User.objects.filter(email=phone_number).first()
            else:
                user = User.objects.filter(phone_number=phone_number).first()
            
            if user:
                user.set_password(new_password)
                user.save()
                
                return Response({
                    'success': True,
                    'message': 'Password reset successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def patch(self, request):
        user = request.user
        allowed_fields = ['full_name', 'location', 'vehicle_type', 'vehicle_number', 'license_number']
        
        for field in allowed_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        
        user.save()
        serializer = UserSerializer(user)
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'data': serializer.data
        })

class TokenRefreshView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'success': True,
                'access_token': str(refresh.access_token)
            })
        except Exception:
            return Response({
                'success': False,
                'message': 'Invalid refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({
                'success': True,
                'message': 'Logged out successfully'
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                'success': False,
                'message': 'Logout failed'
            }, status=status.HTTP_400_BAD_REQUEST)

# =========================================================
# USER MANAGEMENT VIEWS
# =========================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list(request):
    """List all users (Admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'success': False,
            'message': 'You do not have permission to view all users'
        }, status=status.HTTP_403_FORBIDDEN)
    
    users = User.objects.all().order_by('-date_joined')
    
    user_type = request.GET.get('user_type')
    if user_type:
        users = users.filter(user_type=user_type)
    
    is_verified = request.GET.get('is_verified')
    if is_verified is not None:
        if is_verified.lower() == 'true':
            users = users.filter(is_verified=True)
        elif is_verified.lower() == 'false':
            users = users.filter(is_verified=False)
    
    is_active = request.GET.get('is_active')
    if is_active is not None:
        if is_active.lower() == 'true':
            users = users.filter(is_active=True)
        elif is_active.lower() == 'false':
            users = users.filter(is_active=False)
    
    search = request.GET.get('search')
    if search:
        users = users.filter(
            models.Q(full_name__icontains=search) |
            models.Q(phone_number__icontains=search) |
            models.Q(email__icontains=search)
        )
    
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))
    
    total = users.count()
    users = users[offset:offset + limit]
    
    serializer = UserSerializer(users, many=True)
    return Response({
        'success': True,
        'data': {
            'users': serializer.data,
            'total': total,
            'limit': limit,
            'offset': offset,
        }
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """Get user statistics (Admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'success': False,
            'message': 'You do not have permission to view user statistics'
        }, status=status.HTTP_403_FORBIDDEN)
    
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    verified_users = User.objects.filter(is_verified=True).count()
    
    users_by_type = {}
    user_types = ['customer', 'driver', 'station_owner', 'admin']
    for user_type in user_types:
        users_by_type[user_type] = User.objects.filter(user_type=user_type).count()
    
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    new_users_this_month = User.objects.filter(date_joined__date__gte=first_day_of_month).count()
    
    daily_users = []
    for i in range(7):
        date = today - timedelta(days=i)
        count = User.objects.filter(date_joined__date=date).count()
        daily_users.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    return Response({
        'success': True,
        'data': {
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
            'users_by_type': users_by_type,
            'new_users_this_month': new_users_this_month,
            'daily_users': daily_users
        }
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_detail(request, user_id):
    """Get a specific user's details (Admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'success': False,
            'message': 'You do not have permission to view this user'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)
        
        total_orders = Order.objects.filter(user=user).count()
        total_payments = Payment.objects.filter(user=user, status='completed').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        return Response({
            'success': True,
            'data': {
                'user': serializer.data,
                'stats': {
                    'total_orders': total_orders,
                    'total_spent': float(total_payments),
                    'member_since': user.date_joined.strftime('%B %d, %Y'),
                    'last_active': user.last_activity.strftime('%B %d, %Y %H:%M') if user.last_activity else 'Never',
                }
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_update(request, user_id):
    """Update a user (Admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'success': False,
            'message': 'You do not have permission to update this user'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        
        allowed_fields = [
            'full_name', 'email', 'phone_number', 'user_type', 
            'is_active', 'is_verified', 'is_staff', 'is_superuser',
            'location', 'vehicle_type', 'vehicle_number', 'license_number'
        ]
        
        for field in allowed_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        
        if 'password' in request.data and request.data['password']:
            user.set_password(request.data['password'])
        
        user.save()
        
        serializer = UserSerializer(user)
        return Response({
            'success': True,
            'message': 'User updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def user_delete(request, user_id):
    """Delete a user (Admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'success': False,
            'message': 'You do not have permission to delete this user'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        
        if user.id == request.user.id:
            return Response({
                'success': False,
                'message': 'You cannot delete your own account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.delete()
        return Response({
            'success': True,
            'message': f'User {user.full_name} deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_create(request):
    """Create a new user (Admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'success': False,
            'message': 'You do not have permission to create users'
        }, status=status.HTTP_403_FORBIDDEN)
    
    required_fields = ['full_name', 'phone_number', 'email', 'password']
    for field in required_fields:
        if not request.data.get(field):
            return Response({
                'success': False,
                'message': f'{field} is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(phone_number=request.data['phone_number']).exists():
        return Response({
            'success': False,
            'message': 'User with this phone number already exists'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=request.data['email']).exists():
        return Response({
            'success': False,
            'message': 'User with this email already exists'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.create_user(
            phone_number=request.data['phone_number'],
            email=request.data['email'],
            full_name=request.data['full_name'],
            password=request.data['password'],
            user_type=request.data.get('user_type', 'customer'),
            is_active=request.data.get('is_active', True),
            is_verified=request.data.get('is_verified', False),
            location=request.data.get('location', ''),
            vehicle_type=request.data.get('vehicle_type', ''),
            vehicle_number=request.data.get('vehicle_number', ''),
            license_number=request.data.get('license_number', ''),
        )
        
        if request.data.get('is_staff'):
            user.is_staff = request.data['is_staff']
        if request.data.get('is_superuser'):
            user.is_superuser = request.data['is_superuser']
        user.save()
        
        serializer = UserSerializer(user)
        return Response({
            'success': True,
            'message': 'User created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error creating user: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_toggle_active(request, user_id):
    """Toggle user active status (Admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'success': False,
            'message': 'You do not have permission to modify this user'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        
        if user.id == request.user.id:
            return Response({
                'success': False,
                'message': 'You cannot modify your own account status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_active = not user.is_active
        user.save()
        
        return Response({
            'success': True,
            'message': f'User {user.full_name} is now {"active" if user.is_active else "inactive"}',
            'data': {
                'user_id': user.id,
                'is_active': user.is_active
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)

# =========================================================
# DASHBOARD API VIEWS
# =========================================================

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        orders = Order.objects.filter(user=user).order_by('-created_at')[:10]
        total_orders = Order.objects.filter(user=user).count()
        active_orders = Order.objects.filter(user=user, status__in=['pending', 'processing', 'shipped']).count()
        
        recommended_stations = Station.objects.filter(is_open=True).order_by('-rating')[:5]
        
        notifications = Notification.objects.filter(user=user, is_read=False)[:5]
        
        data = {
            'total_orders': total_orders,
            'active_orders': active_orders,
            'recent_orders': OrderSerializer(orders, many=True).data,
            'recommended_stations': StationSerializer(recommended_stations, many=True).data,
            'notifications': NotificationSerializer(notifications, many=True).data,
            'user': UserSerializer(user).data,
        }
        
        return Response({
            'success': True,
            'data': data
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    total_stations = Station.objects.count()
    active_stations = Station.objects.filter(is_open=True).count()
    total_agents = DeliveryAgent.objects.count()
    active_agents = DeliveryAgent.objects.filter(status='available').count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='delivered').count()
    
    total_revenue = Payment.objects.filter(status='completed').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    week_revenue = Payment.objects.filter(
        status='completed',
        created_at__gte=week_ago
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    recent_orders = Order.objects.order_by('-created_at')[:5]
    unread_notifications = Notification.objects.filter(is_read=False).count()
    total_vehicles = Vehicle.objects.count()
    vehicles_in_maintenance = Vehicle.objects.filter(status='maintenance').count()
    
    data = {
        'total_stations': total_stations,
        'active_stations': active_stations,
        'total_agents': total_agents,
        'active_agents': active_agents,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_revenue': float(total_revenue),
        'week_revenue': float(week_revenue),
        'recent_orders': OrderSerializer(recent_orders, many=True).data,
        'unread_notifications': unread_notifications,
        'total_vehicles': total_vehicles,
        'vehicles_in_maintenance': vehicles_in_maintenance,
    }
    
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_chart_data(request):
    """Get chart data for dashboard"""
    days = int(request.GET.get('days', 7))
    start_date = timezone.now().date() - timedelta(days=days)
    
    order_data = []
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        
        orders = Order.objects.filter(
            created_at__date=date
        ).count()
        
        revenue = Payment.objects.filter(
            status='completed',
            created_at__date=date
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        order_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'orders': orders,
            'revenue': float(revenue)
        })
    
    return Response({
        'order_data': order_data,
    })

# =========================================================
# STATION API VIEWS - UPDATED WITH IMAGE URLS (FIXED)
# =========================================================

class StationsView(APIView):
    """Get all stations with full image URLs"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        stations = Station.objects.all()
        
        search = request.query_params.get('search', None)
        if search:
            stations = stations.filter(
                models.Q(name__icontains=search) | 
                models.Q(address__icontains=search)
            )
        
        fuel_type = request.query_params.get('fuel_type', None)
        if fuel_type:
            stations = stations.filter(fuel_types__icontains=fuel_type)
        
        is_open = request.query_params.get('is_open', None)
        if is_open is not None:
            if is_open.lower() == 'true':
                stations = stations.filter(is_open=True)
            elif is_open.lower() == 'false':
                stations = stations.filter(is_open=False)
        
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        total = stations.count()
        stations = stations[offset:offset + limit]
        
        # Build response with full image URLs
        station_data = []
        for station in stations:
            # Get full image URL - IMPORTANT FIX
            image_url = ''
            if station.image:
                # Check if it's already a full URL
                if station.image.startswith('http'):
                    image_url = station.image
                else:
                    # Build absolute URL for the image
                    image_url = request.build_absolute_uri('/media/' + station.image)
            
            station_data.append({
                'id': str(station.id),
                'name': station.name,
                'address': station.address,
                'location': station.address,  # For backward compatibility
                'rating': float(station.rating) if station.rating else 0,
                'reviews_count': station.reviews_count or 0,
                'is_open': station.is_open,
                'is_24_7': station.is_24_7,
                'price_per_gallon': float(station.price_per_gallon) if station.price_per_gallon else 0,
                'fuel_types': station.fuel_types or 'Petrol,Diesel,Gas',
                'image': image_url,  # Full URL
                'latitude': float(station.latitude) if station.latitude else None,
                'longitude': float(station.longitude) if station.longitude else None,
                'phone': station.phone or '',
                'email': station.email or '',
            })
        
        return Response({
            'success': True,
            'data': {
                'stations': station_data,
                'total': total,
                'limit': limit,
                'offset': offset,
            }
        }, status=status.HTTP_200_OK)


class TopStationsView(APIView):
    """Get top rated stations with full image URLs"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        stations = Station.objects.filter(is_open=True).order_by('-rating')[:10]
        
        station_data = []
        for station in stations:
            # Get full image URL - IMPORTANT FIX
            image_url = ''
            if station.image:
                # Check if it's already a full URL
                if station.image.startswith('http'):
                    image_url = station.image
                else:
                    # Build absolute URL for the image
                    image_url = request.build_absolute_uri('/media/' + station.image)
            
            station_data.append({
                'id': str(station.id),
                'name': station.name,
                'address': station.address,
                'location': station.address,  # For backward compatibility
                'rating': float(station.rating) if station.rating else 0,
                'reviews_count': station.reviews_count or 0,
                'is_open': station.is_open,
                'is_24_7': station.is_24_7,
                'price_per_gallon': float(station.price_per_gallon) if station.price_per_gallon else 0,
                'fuel_types': station.fuel_types or 'Petrol,Diesel,Gas',
                'image': image_url,  # Full URL
                'latitude': float(station.latitude) if station.latitude else None,
                'longitude': float(station.longitude) if station.longitude else None,
                'phone': station.phone or '',
                'email': station.email or '',
            })
        
        return Response({
            'success': True,
            'data': station_data
        }, status=status.HTTP_200_OK)


# =========================================================
# STATION API VIEWS - REST
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def station_list_create(request):
    """List all stations or create a new station"""
    if request.method == 'GET':
        stations = Station.objects.all()
        serializer = StationSerializer(stations, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to create stations'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StationDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, station_id):
        try:
            station = Station.objects.get(id=station_id)
            return Response({
                'success': True,
                'data': StationDetailSerializer(station).data
            }, status=status.HTTP_200_OK)
        except Station.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Station not found'
            }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def station_detail(request, pk):
    """Get, update or delete a station"""
    try:
        station = Station.objects.get(pk=pk)
    except Station.DoesNotExist:
        return Response({'error': 'Station not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = StationSerializer(station)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to update stations'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StationSerializer(station, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to delete stations'
            }, status=status.HTTP_403_FORBIDDEN)
        
        station.delete()
        return Response({'message': 'Station deleted'}, status=status.HTTP_204_NO_CONTENT)


# =========================================================
# STATION MANAGEMENT VIEWS
# =========================================================

class StationManagementView(APIView):
    """View for managing stations (CRUD operations)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all stations with optional filtering"""
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to manage stations'
            }, status=status.HTTP_403_FORBIDDEN)
        
        stations = Station.objects.all()
        
        search = request.query_params.get('search', None)
        if search:
            stations = stations.filter(
                models.Q(name__icontains=search) | 
                models.Q(address__icontains=search)
            )
        
        status_filter = request.query_params.get('status', None)
        if status_filter == 'open':
            stations = stations.filter(is_open=True)
        elif status_filter == 'closed':
            stations = stations.filter(is_open=False)
        
        fuel_type = request.query_params.get('fuel_type', None)
        if fuel_type:
            stations = stations.filter(fuel_types__icontains=fuel_type)
        
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        
        total = stations.count()
        stations = stations[offset:offset + limit]
        
        return Response({
            'success': True,
            'data': {
                'stations': StationSerializer(stations, many=True).data,
                'total': total,
                'limit': limit,
                'offset': offset,
            }
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new station"""
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to create stations'
            }, status=status.HTTP_403_FORBIDDEN)
        
        required_fields = ['name', 'address']
        for field in required_fields:
            if not request.data.get(field):
                return Response({
                    'success': False,
                    'message': f'{field} is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            station = Station.objects.create(
                name=request.data.get('name'),
                address=request.data.get('address'),
                latitude=request.data.get('latitude'),
                longitude=request.data.get('longitude'),
                rating=request.data.get('rating', 4.0),
                reviews_count=request.data.get('reviews_count', 0),
                image=request.data.get('image', ''),
                is_open=request.data.get('is_open', True),
                is_24_7=request.data.get('is_24_7', False),
                price_per_gallon=request.data.get('price_per_gallon', 3.60),
                fuel_types=request.data.get('fuel_types', 'Petrol,Diesel,Gas'),
                phone=request.data.get('phone', ''),
                email=request.data.get('email', ''),
            )
            
            return Response({
                'success': True,
                'message': 'Station created successfully',
                'data': StationDetailSerializer(station).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error creating station: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        """Update an existing station"""
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to update stations'
            }, status=status.HTTP_403_FORBIDDEN)
        
        station_id = request.data.get('id')
        if not station_id:
            return Response({
                'success': False,
                'message': 'Station ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            station = Station.objects.get(id=station_id)
            
            station.name = request.data.get('name', station.name)
            station.address = request.data.get('address', station.address)
            station.latitude = request.data.get('latitude', station.latitude)
            station.longitude = request.data.get('longitude', station.longitude)
            station.rating = request.data.get('rating', station.rating)
            station.reviews_count = request.data.get('reviews_count', station.reviews_count)
            station.image = request.data.get('image', station.image)
            station.is_open = request.data.get('is_open', station.is_open)
            station.is_24_7 = request.data.get('is_24_7', station.is_24_7)
            station.price_per_gallon = request.data.get('price_per_gallon', station.price_per_gallon)
            station.fuel_types = request.data.get('fuel_types', station.fuel_types)
            station.phone = request.data.get('phone', station.phone)
            station.email = request.data.get('email', station.email)
            station.save()
            
            return Response({
                'success': True,
                'message': 'Station updated successfully',
                'data': StationDetailSerializer(station).data
            }, status=status.HTTP_200_OK)
            
        except Station.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Station not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error updating station: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """Delete a station"""
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to delete stations'
            }, status=status.HTTP_403_FORBIDDEN)
        
        station_id = request.data.get('id')
        if not station_id:
            return Response({
                'success': False,
                'message': 'Station ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            station = Station.objects.get(id=station_id)
            station.delete()
            return Response({
                'success': True,
                'message': 'Station deleted successfully'
            }, status=status.HTTP_200_OK)
        except Station.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Station not found'
            }, status=status.HTTP_404_NOT_FOUND)

# =========================================================
# ORDER API VIEWS
# =========================================================

class OrdersView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        
        status_filter = request.query_params.get('status', None)
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        total = orders.count()
        orders = orders[offset:offset + limit]
        
        return Response({
            'success': True,
            'data': {
                'orders': OrderSerializer(orders, many=True).data,
                'total': total,
                'limit': limit,
                'offset': offset,
            }
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list(request):
    """List all orders with filters"""
    orders = Order.objects.all()
    
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    date_from = request.GET.get('date_from')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    """Get order details"""
    try:
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = OrderSerializer(order)
    return Response(serializer.data)

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        station_id = request.data.get('station_id')
        fuel_type = request.data.get('fuel_type')
        quantity = request.data.get('quantity')
        delivery_location = request.data.get('delivery_location')
        
        if not all([station_id, fuel_type, quantity, delivery_location]):
            return Response({
                'success': False,
                'message': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            station = Station.objects.get(id=station_id)
        except Station.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Station not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        total_amount = float(quantity) * float(station.price_per_gallon)
        
        order = Order.objects.create(
            user=request.user,
            station=station,
            fuel_type=fuel_type,
            quantity=quantity,
            total_amount=total_amount,
            delivery_location=delivery_location,
            status='pending'
        )
        
        Notification.objects.create(
            user=request.user,
            title='Order Created',
            message=f'Your order #{order.order_reference} has been created successfully.',
            type='order'
        )
        
        return Response({
            'success': True,
            'message': 'Order created successfully',
            'data': OrderSerializer(order).data
        }, status=status.HTTP_201_CREATED)

# =========================================================
# NOTIFICATION API VIEWS
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def notification_list_create(request):
    """List notifications or create a new notification"""
    if request.method == 'GET':
        if request.user.is_staff or request.user.is_superuser:
            notifications = Notification.objects.all().order_by('-created_at')
        else:
            notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        
        is_read = request.GET.get('is_read')
        if is_read is not None:
            if is_read.lower() == 'true':
                notifications = notifications.filter(is_read=True)
            elif is_read.lower() == 'false':
                notifications = notifications.filter(is_read=False)
        
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        
        total = notifications.count()
        notifications = notifications[offset:offset + limit]
        
        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            'success': True,
            'data': {
                'notifications': serializer.data,
                'total': total,
                'limit': limit,
                'offset': offset,
            }
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to create notifications'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Notification created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def notification_mark_read(request, pk):
    """Mark a notification as read"""
    try:
        if request.user.is_staff or request.user.is_superuser:
            notification = Notification.objects.get(pk=pk)
        else:
            notification = Notification.objects.get(pk=pk, user=request.user)
        
        notification.is_read = True
        notification.save()
        return Response({
            'success': True,
            'message': 'Notification marked as read'
        }, status=status.HTTP_200_OK)
        
    except Notification.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)

# =========================================================
# PAYMENT API VIEWS
# =========================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_list(request):
    """List all payments (Admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({
            'success': False,
            'message': 'You do not have permission to view payments'
        }, status=status.HTTP_403_FORBIDDEN)
    
    payments = Payment.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    date_from = request.GET.get('date_from')
    if date_from:
        payments = payments.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        payments = payments.filter(created_at__date__lte=date_to)
    
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))
    
    total = payments.count()
    payments = payments[offset:offset + limit]
    
    serializer = PaymentSerializer(payments, many=True)
    return Response({
        'success': True,
        'data': {
            'payments': serializer.data,
            'total': total,
            'limit': limit,
            'offset': offset,
        }
    }, status=status.HTTP_200_OK)

# =========================================================
# VEHICLE API VIEWS
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def vehicle_list_create(request):
    """List all vehicles or create a new vehicle"""
    if request.method == 'GET':
        vehicles = Vehicle.objects.all()
        
        status_filter = request.GET.get('status')
        if status_filter:
            vehicles = vehicles.filter(status=status_filter)
        
        search = request.GET.get('search')
        if search:
            vehicles = vehicles.filter(
                models.Q(name__icontains=search) |
                models.Q(vin__icontains=search) |
                models.Q(license_plate__icontains=search) |
                models.Q(driver_name__icontains=search)
            )
        
        serializer = VehicleSerializer(vehicles, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to create vehicles'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = VehicleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def vehicle_detail(request, pk):
    """Get, update or delete a vehicle"""
    try:
        vehicle = Vehicle.objects.get(pk=pk)
    except Vehicle.DoesNotExist:
        return Response({'error': 'Vehicle not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = VehicleSerializer(vehicle)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to update vehicles'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = VehicleSerializer(vehicle, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to delete vehicles'
            }, status=status.HTTP_403_FORBIDDEN)
        
        vehicle.delete()
        return Response({'message': 'Vehicle deleted'}, status=status.HTTP_204_NO_CONTENT)

class VehicleListView(APIView):
    """List all vehicles with filters"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        vehicles = Vehicle.objects.all()
        
        status_filter = request.query_params.get('status', None)
        if status_filter:
            vehicles = vehicles.filter(status=status_filter)
        
        search = request.query_params.get('search', None)
        if search:
            vehicles = vehicles.filter(
                models.Q(name__icontains=search) |
                models.Q(vin__icontains=search) |
                models.Q(license_plate__icontains=search) |
                models.Q(driver_name__icontains=search)
            )
        
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        total = vehicles.count()
        vehicles = vehicles[offset:offset + limit]
        
        return Response({
            'success': True,
            'data': {
                'vehicles': VehicleSerializer(vehicles, many=True).data,
                'total': total,
                'limit': limit,
                'offset': offset,
            }
        }, status=status.HTTP_200_OK)

class VehicleCRUDView(APIView):
    """Create, Update, Delete vehicles"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to create vehicles'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = VehicleSerializer(data=request.data)
        if serializer.is_valid():
            vehicle = serializer.save()
            return Response({
                'success': True,
                'message': 'Vehicle created successfully',
                'data': VehicleSerializer(vehicle).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, vehicle_id):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to update vehicles'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            serializer = VehicleSerializer(vehicle, data=request.data, partial=True)
            if serializer.is_valid():
                vehicle = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Vehicle updated successfully',
                    'data': VehicleSerializer(vehicle).data
                }, status=status.HTTP_200_OK)
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Vehicle.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Vehicle not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, vehicle_id):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({
                'success': False,
                'message': 'You do not have permission to delete vehicles'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            vehicle.delete()
            return Response({
                'success': True,
                'message': 'Vehicle deleted successfully'
            }, status=status.HTTP_200_OK)
        except Vehicle.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Vehicle not found'
            }, status=status.HTTP_404_NOT_FOUND)

class VehicleDashboardView(APIView):
    """Get vehicle dashboard data"""
    permission_classes = [AllowAny]
    
    def get(self, request, vehicle_id=None):
        try:
            if vehicle_id:
                vehicle = Vehicle.objects.get(id=vehicle_id)
            else:
                vehicle = Vehicle.objects.first()
                if not vehicle:
                    return Response({
                        'success': False,
                        'message': 'No vehicles found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            costs = VehicleCost.objects.filter(vehicle=vehicle)
            total_cost = sum(c.amount for c in costs if c.cost_type == 'total')
            service_cost = sum(c.amount for c in costs if c.cost_type == 'service')
            other_cost = sum(c.amount for c in costs if c.cost_type == 'other')
            
            issues = VehicleIssue.objects.filter(vehicle=vehicle)
            overdue_issues = issues.filter(is_overdue=True).count()
            open_issues = issues.filter(is_open=True).count()
            
            meter_history = VehicleMeterHistory.objects.filter(vehicle=vehicle)[:12]
            meter_usage = [m.reading for m in meter_history] if meter_history else [7200, 7500, 7800, 8100, 8400, 8700, 9000, 9300, 9600, 9900, 10200, 10500]
            
            data = {
                'vehicle': VehicleSerializer(vehicle).data,
                'total_cost': total_cost,
                'service_cost': service_cost,
                'other_cost': other_cost,
                'overdue_issues': overdue_issues,
                'open_issues': open_issues,
                'meter_usage': meter_usage,
            }
            
            return Response({
                'success': True,
                'data': data
            }, status=status.HTTP_200_OK)
            
        except Vehicle.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Vehicle not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)