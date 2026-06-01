from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('stations/', views.dashboard_stations, name='stations'),
    path('users/', views.dashboard_users, name='users'),

    path('partials/stations/table/', views.station_table_partial, name='station_table_partial'),
    path('partials/toast/<str:message_type>/', views.toast_message, name='toast'),

    path('stations/create/', views.dashboard_stations, name='create_station_modal'),
    path('stations/<int:pk>/edit/', views.dashboard_stations, name='edit_station_modal'),
]