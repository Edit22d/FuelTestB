from django.urls import path
from . import views

urlpatterns = [
    # Auth endpoints
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/social/', views.SocialLoginView.as_view(), name='social_login'),
    path('auth/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),
    
    # User profile
    path('user/profile/', views.UserProfileView.as_view(), name='user_profile'),
    
    # Dashboard endpoints
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('stations/', views.StationsView.as_view(), name='stations'),
    path('stations/<int:station_id>/', views.StationDetailView.as_view(), name='station_detail'),
    path('stations/top/', views.TopStationsView.as_view(), name='top_stations'),
    path('orders/', views.OrdersView.as_view(), name='orders'),
    path('orders/create/', views.CreateOrderView.as_view(), name='create_order'),
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
    path('stations/manage/', views.StationManagementView.as_view(), name='station_management'),
     # Vehicle Dashboard
    path('vehicles/dashboard/<int:vehicle_id>/', views.VehicleDashboardView.as_view(), name='vehicle_dashboard'),
    path('vehicles/dashboard/', views.VehicleDashboardView.as_view(), name='vehicle_dashboard_default'),
    path('vehicles/list/', views.VehicleListView.as_view(), name='vehicle_list'),
    path('vehicles/', views.VehicleCRUDView.as_view(), name='vehicle_crud'),
    path('vehicles/<int:vehicle_id>/', views.VehicleCRUDView.as_view(), name='vehicle_crud_detail'),
]