from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.utils.html import format_html
import uuid
import requests
import json
import random
import traceback

from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer
)
from .models import User, LoginHistory

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
    """Send password reset email with OTP - Modern HTML Version"""
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
                background: linear-gradient(135deg, #f5a623, #f7c948);
                padding: 30px 40px;
                text-align: center;
            }}
            .header h1 {{
                color: #ffffff;
                font-size: 24px;
                font-weight: 700;
                margin: 0;
                letter-spacing: 0.5px;
            }}
            .header p {{
                color: rgba(255,255,255,0.9);
                font-size: 14px;
                margin: 8px 0 0;
            }}
            .content {{
                padding: 40px;
            }}
            .content h2 {{
                color: #1a2a3a;
                font-size: 20px;
                font-weight: 600;
                margin: 0 0 12px;
            }}
            .content p {{
                color: #4a5568;
                font-size: 15px;
                line-height: 1.6;
                margin: 0 0 16px;
            }}
            .token-box {{
                background: linear-gradient(135deg, #f7fafc, #edf2f7);
                border: 2px dashed #f5a623;
                border-radius: 16px;
                padding: 24px;
                text-align: center;
                margin: 24px 0;
                position: relative;
            }}
            .token-box .label {{
                color: #718096;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 600;
            }}
            .token-box .token {{
                font-family: 'Courier New', monospace;
                font-size: 32px;
                font-weight: 700;
                color: #1a2a3a;
                letter-spacing: 4px;
                padding: 12px 0;
                display: block;
                background: #ffffff;
                border-radius: 8px;
                margin-top: 8px;
            }}
            .token-box .copy-hint {{
                color: #a0aec0;
                font-size: 12px;
                margin-top: 8px;
            }}
            .info-row {{
                display: flex;
                align-items: center;
                gap: 12px;
                background: #f7fafc;
                padding: 12px 16px;
                border-radius: 10px;
                margin: 16px 0;
            }}
            .info-row .icon {{
                font-size: 18px;
            }}
            .info-row .text {{
                color: #4a5568;
                font-size: 13px;
            }}
            .divider {{
                border-top: 1px solid #e2e8f0;
                margin: 24px 0;
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
                line-height: 1.6;
            }}
            .footer a {{
                color: #f5a623;
                text-decoration: none;
            }}
            .badge {{
                display: inline-block;
                background: #48bb78;
                color: #ffffff;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 12px;
                border-radius: 20px;
                margin-top: 4px;
            }}
            .expiry {{
                color: #e53e3e;
                font-weight: 500;
                font-size: 13px;
            }}
            @media (max-width: 480px) {{
                .container {{
                    margin: 20px 16px;
                }}
                .header {{
                    padding: 20px;
                }}
                .content {{
                    padding: 24px;
                }}
                .token-box .token {{
                    font-size: 24px;
                    letter-spacing: 2px;
                }}
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
                <p>We received a request to reset the password for your Fuel Connect account. Use the verification code below to continue.</p>
                <div class="token-box">
                    <div class="label">🔑 Verification Code</div>
                    <span class="token">{reset_token}</span>
                    <div class="copy-hint">📋 Tap or click the code to copy it</div>
                </div>
                <div class="info-row">
                    <span class="icon">⏱️</span>
                    <span class="text">This code will expire in <strong>5 minutes</strong></span>
                </div>
                <div class="info-row">
                    <span class="icon">🛡️</span>
                    <span class="text">For your security, never share this code with anyone</span>
                </div>
                <div class="divider"></div>
                <p style="font-size: 14px; color: #718096;">
                    <strong>📌 How to use this code:</strong>
                </p>
                <ol style="color: #4a5568; font-size: 14px; line-height: 1.8; padding-left: 20px;">
                    <li>Open the Fuel Connect app</li>
                    <li>Enter the verification code shown above</li>
                    <li>Create your new password</li>
                </ol>
                <div style="background: #fefcbf; border-left: 4px solid #f5a623; padding: 12px 16px; border-radius: 8px; margin-top: 16px;">
                    <p style="color: #744210; font-size: 13px; margin: 0;">
                        <strong>⚠️ Important:</strong> If you didn't request this, please ignore this email. Your account remains secure.
                    </p>
                </div>
            </div>
            <div class="footer">
                <p>
                    <strong>Fuel Connect</strong> — Smart Fuel Tracking
                </p>
                <p style="margin-top: 8px;">
                    This is an automated message, please do not reply.
                </p>
                <p style="margin-top: 8px;">
                    &copy; 2026 Fuel Connect. All rights reserved.
                </p>
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
# VIEWS
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
                    'message': 'Security verification required. Please solve the math problem.',
                    'requires_captcha': True,
                    'error': 'captcha_required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if captcha_token and needs_captcha:
                if not captcha_token.startswith('math_captcha_'):
                    return Response({
                        'success': False,
                        'message': 'Invalid verification. Please try again.',
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
        
        error_data = serializer.errors.get('non_field_errors', [{}])[0] if serializer.errors.get('non_field_errors') else {}
        
        try:
            User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No account found with this phone number. Please sign up first.',
                'error': 'account_not_found'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = User.objects.get(phone_number=phone_number)
            if user.is_locked():
                remaining = user.get_lockout_time_remaining()
                minutes = remaining // 60
                return Response({
                    'success': False,
                    'message': f'Account locked. Too many failed attempts. Please try again in {minutes} minutes.',
                    'error': 'account_locked',
                    'lockout_seconds': remaining
                }, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            pass
        
        if isinstance(error_data, dict):
            return Response({
                'success': False,
                'message': error_data.get('message', 'Invalid credentials'),
                'error': error_data.get('error', 'invalid_credentials'),
                'remaining_attempts': error_data.get('remaining_attempts'),
                'lockout_seconds': error_data.get('lockout_seconds')
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'success': False,
            'message': 'Invalid phone number or password',
            'error': 'invalid_credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

# =========================================================
# UPDATED SocialLoginView - Accepts both id_token and access_token
# =========================================================

class SocialLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        provider = request.data.get('provider')
        access_token = request.data.get('access_token')
        id_token = request.data.get('id_token')  # Also accept id_token
        
        # Use id_token if available, otherwise use access_token
        token = id_token or access_token
        
        print(f"📡 Provider: {provider}")
        print(f"📡 Token: {token[:50] if token else 'None'}...")
        
        if not provider or not token:
            return Response({
                'success': False,
                'message': 'Provider and token are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = None
            
            if provider == 'google':
                # Try both token types
                google_data = None
                token_used = None
                
                # Try with id_token first
                if id_token:
                    try:
                        google_url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={id_token}"
                        response = requests.get(google_url, timeout=10)
                        if response.status_code == 200:
                            google_data = response.json()
                            token_used = 'id_token'
                    except Exception as e:
                        print(f"id_token verification failed: {e}")
                
                # If id_token failed, try with access_token
                if not google_data and access_token:
                    try:
                        google_url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}"
                        response = requests.get(google_url, timeout=10)
                        if response.status_code == 200:
                            google_data = response.json()
                            token_used = 'access_token'
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
                    
                    print(f"✅ Google login successful using {token_used}")
                else:
                    print(f"❌ Google token invalid - response: {google_data}")
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
                'message': 'Invalid or expired token. Please use the 6-digit code sent to your email.'
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

# Add these imports at the top
from .models import Station, FuelPrice, Order, Notification
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer, 
    StationSerializer, StationDetailSerializer, FuelPriceSerializer,
    OrderSerializer, NotificationSerializer, DashboardDataSerializer
)

# =========================================================
# DASHBOARD VIEWS
# =========================================================

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get orders
        orders = Order.objects.filter(user=user).order_by('-created_at')[:10]
        total_orders = Order.objects.filter(user=user).count()
        active_orders = Order.objects.filter(user=user, status__in=['pending', 'processing', 'shipped']).count()
        
        # Get recommended stations (top rated)
        recommended_stations = Station.objects.filter(is_open=True).order_by('-rating')[:5]
        
        # Get notifications
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

class StationsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        stations = Station.objects.all()
        
        # Filter by search query
        search = request.query_params.get('search', None)
        if search:
            stations = stations.filter(
                models.Q(name__icontains=search) | 
                models.Q(location__icontains=search) |
                models.Q(address__icontains=search)
            )
        
        # Filter by fuel type
        fuel_type = request.query_params.get('fuel_type', None)
        if fuel_type:
            stations = stations.filter(fuel_types__icontains=fuel_type)
        
        # Filter by open/closed
        is_open = request.query_params.get('is_open', None)
        if is_open is not None:
            if is_open.lower() == 'true':
                stations = stations.filter(is_open=True)
            elif is_open.lower() == 'false':
                stations = stations.filter(is_open=False)
        
        # Pagination
        limit = int(request.query_params.get('limit', 20))
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

class TopStationsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        stations = Station.objects.filter(is_open=True).order_by('-rating')[:10]
        
        return Response({
            'success': True,
            'data': StationSerializer(stations, many=True).data
        }, status=status.HTTP_200_OK)

class OrdersView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        
        # Filter by status
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
        
        # Calculate total amount (example: $3.60 per gallon)
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
        
        # Create notification
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

class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
        
        return Response({
            'success': True,
            'data': NotificationSerializer(notifications, many=True).data
        }, status=status.HTTP_200_OK)
    
    def patch(self, request):
        notification_id = request.data.get('notification_id')
        if notification_id:
            try:
                notification = Notification.objects.get(id=notification_id, user=request.user)
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
        
        # Mark all as read
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({
            'success': True,
            'message': 'All notifications marked as read'
        }, status=status.HTTP_200_OK)

# Add these views for station management

class StationManagementView(APIView):
    """View for managing stations (CRUD operations)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get all stations with optional filtering
        stations = Station.objects.all()
        
        # Filter by search
        search = request.query_params.get('search', None)
        if search:
            stations = stations.filter(
                models.Q(name__icontains=search) | 
                models.Q(location__icontains=search) |
                models.Q(address__icontains=search)
            )
        
        # Filter by status
        status_filter = request.query_params.get('status', None)
        if status_filter == 'open':
            stations = stations.filter(is_open=True)
        elif status_filter == 'closed':
            stations = stations.filter(is_open=False)
        
        # Pagination
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
        # Validate required fields
        required_fields = ['name', 'location', 'address']
        for field in required_fields:
            if not request.data.get(field):
                return Response({
                    'success': False,
                    'message': f'{field} is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            station = Station.objects.create(
                name=request.data.get('name'),
                location=request.data.get('location'),
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
            )
            
            # Add fuel prices if provided
            prices = request.data.get('prices', [])
            for price_data in prices:
                FuelPrice.objects.create(
                    station=station,
                    fuel_type=price_data.get('fuel_type', 'petrol'),
                    price=price_data.get('price', 0)
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
        station_id = request.data.get('id')
        if not station_id:
            return Response({
                'success': False,
                'message': 'Station ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            station = Station.objects.get(id=station_id)
            
            # Update fields
            station.name = request.data.get('name', station.name)
            station.location = request.data.get('location', station.location)
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

# Add these imports at the top
from .models import Vehicle, VehicleCost, VehicleIssue, VehicleMeterHistory
from .serializers import (
    # ... existing imports
    VehicleSerializer, VehicleDetailSerializer, 
    VehicleDashboardDataSerializer, VehicleCostSerializer,
    VehicleIssueSerializer
)

class VehicleDashboardView(APIView):
    """Get vehicle dashboard data"""
    permission_classes = [AllowAny]
    
    def get(self, request, vehicle_id=None):
        try:
            if vehicle_id:
                vehicle = Vehicle.objects.get(id=vehicle_id)
            else:
                # Get first vehicle or most recent
                vehicle = Vehicle.objects.first()
                if not vehicle:
                    return Response({
                        'success': False,
                        'message': 'No vehicles found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Get costs
            costs = VehicleCost.objects.filter(vehicle=vehicle)
            total_cost = sum(c.amount for c in costs if c.cost_type == 'total')
            service_cost = sum(c.amount for c in costs if c.cost_type == 'service')
            other_cost = sum(c.amount for c in costs if c.cost_type == 'other')
            
            # Get issues
            issues = VehicleIssue.objects.filter(vehicle=vehicle)
            overdue_issues = issues.filter(is_overdue=True).count()
            open_issues = issues.filter(is_open=True).count()
            total_issues = issues.count()
            
            # Get meter history (last 12 readings)
            meter_history = VehicleMeterHistory.objects.filter(vehicle=vehicle)[:12]
            meter_usage = [m.reading for m in meter_history] if meter_history else [7200, 7500, 7800, 8100, 8400, 8700, 9000, 9300, 9600, 9900, 10200, 10500]
            
            data = {
                'vehicle': VehicleSerializer(vehicle).data,
                'total_cost': total_cost,
                'service_cost': service_cost,
                'other_cost': other_cost,
                'overdue_issues': overdue_issues,
                'open_issues': open_issues,
                'total_issues': total_issues,
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

class VehicleListView(APIView):
    """List all vehicles"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        vehicles = Vehicle.objects.all()
        
        # Filter by status
        status_filter = request.query_params.get('status', None)
        if status_filter:
            vehicles = vehicles.filter(status=status_filter)
        
        # Search
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
        # Create new vehicle
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