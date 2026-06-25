# api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # =========================================================
    # AUTHENTICATION ENDPOINTS
    # =========================================================
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/social/', views.SocialLoginView.as_view(), name='social_login'),
    path('auth/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),
    
    # =========================================================
    # USER PROFILE & MANAGEMENT
    # =========================================================
    path('user/profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('users/', views.user_list, name='user_list'),
    path('users/stats/', views.user_stats, name='user_stats'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/update/', views.user_update, name='user_update'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    
    # =========================================================
    # DASHBOARD ENDPOINTS (For Frontend)
    # =========================================================
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('dashboard/chart/', views.dashboard_chart_data, name='dashboard_chart'),
    
    # =========================================================
    # STATION ENDPOINTS (For Frontend)
    # =========================================================
    path('stations/', views.StationsView.as_view(), name='stations'),
    path('stations/all/', views.station_list_create, name='station_list_create'),
    path('stations/top/', views.TopStationsView.as_view(), name='top_stations'),
    path('stations/manage/', views.StationManagementView.as_view(), name='station_management'),
    path('stations/<int:station_id>/', views.StationDetailView.as_view(), name='station_detail'),
    path('stations/<uuid:pk>/', views.station_detail, name='station_detail_uuid'),
    
    # =========================================================
    # VEHICLE ENDPOINTS (For Frontend)
    # =========================================================
    path('vehicles/', views.VehicleCRUDView.as_view(), name='vehicle_crud'),
    path('vehicles/list/', views.VehicleListView.as_view(), name='vehicle_list'),
    path('vehicles/dashboard/', views.VehicleDashboardView.as_view(), name='vehicle_dashboard_default'),
    path('vehicles/dashboard/<int:vehicle_id>/', views.VehicleDashboardView.as_view(), name='vehicle_dashboard'),
    path('vehicles/<uuid:pk>/', views.vehicle_detail, name='vehicle_detail_uuid'),
    path('vehicles/<int:vehicle_id>/', views.VehicleCRUDView.as_view(), name='vehicle_crud_detail'),
    path('vehicles/all/', views.vehicle_list_create, name='vehicle_list_create'),
    
    # =========================================================
    # ORDER ENDPOINTS (For Frontend)
    # =========================================================
    path('orders/', views.OrdersView.as_view(), name='orders'),
    path('orders/all/', views.order_list, name='order_list'),
    path('orders/create/', views.CreateOrderView.as_view(), name='create_order'),
    path('orders/<uuid:pk>/', views.order_detail, name='order_detail'),
    
    # =========================================================
    # NOTIFICATION ENDPOINTS (For Frontend)
    # =========================================================
    path('notifications/', views.notification_list_create, name='notifications'),
    path('notifications/all/', views.notification_list_create, name='notification_list_create'),
    path('notifications/<uuid:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    
    # =========================================================
    # PAYMENT ENDPOINTS (For Frontend)
    # =========================================================
    path('payments/', views.payment_list, name='payment_list'),
]