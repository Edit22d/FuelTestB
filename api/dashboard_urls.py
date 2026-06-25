# api/dashboard_urls.py
from django.urls import path
from . import dashboard_views

urlpatterns = [
    # Dashboard home
    path('', dashboard_views.dashboard_index, name='dashboard_index'),
    
    # Stations - Full CRUD
    path('stations/', dashboard_views.station_list, name='station_list'),
    path('stations/create/', dashboard_views.station_create, name='station_create'),
    path('stations/<uuid:pk>/', dashboard_views.station_detail, name='station_detail'),
    path('stations/<uuid:pk>/edit/', dashboard_views.station_edit, name='station_edit'),
    path('stations/<uuid:pk>/delete/', dashboard_views.station_delete, name='station_delete'),
    
    # Vehicles
    path('vehicles/', dashboard_views.vehicle_list, name='vehicle_list'),
    path('vehicles/create/', dashboard_views.vehicle_create, name='vehicle_create'),
    path('vehicles/<uuid:pk>/edit/', dashboard_views.vehicle_edit, name='vehicle_edit'),
    path('vehicles/<uuid:pk>/delete/', dashboard_views.vehicle_delete, name='vehicle_delete'),
    path('vehicles/<uuid:pk>/', dashboard_views.vehicle_detail, name='vehicle_detail'),
    
    # Orders
    path('orders/', dashboard_views.order_list, name='order_list'),
    path('orders/<uuid:pk>/', dashboard_views.order_detail, name='order_detail'),
    path('orders/<uuid:pk>/update-status/', dashboard_views.order_update_status, name='order_update_status'),
    path('orders/<uuid:pk>/delete/', dashboard_views.order_delete, name='order_delete'),
    
    # Payments
    path('payments/', dashboard_views.payment_list, name='payment_list'),
    path('payments/<uuid:pk>/', dashboard_views.payment_detail, name='payment_detail'),
    
    # Notifications
    path('notifications/', dashboard_views.notification_list, name='notification_list'),
    path('notifications/create/', dashboard_views.notification_create, name='notification_create'),
    path('notifications/mark-all-read/', dashboard_views.notification_mark_all_read, name='notification_mark_all_read'),
    path('notifications/<uuid:pk>/read/', dashboard_views.notification_mark_read, name='notification_mark_read'),
    path('notifications/<uuid:pk>/delete/', dashboard_views.notification_delete, name='notification_delete'),
    
    # Security
    path('security/logs/', dashboard_views.security_logs, name='security_logs'),
    path('security/logs/<uuid:pk>/', dashboard_views.security_log_detail, name='security_log_detail'),
    
    # Users
    path('users/', dashboard_views.user_list, name='user_list'),
    path('users/<int:user_id>/', dashboard_views.user_detail, name='user_detail'),
]