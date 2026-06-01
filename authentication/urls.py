from django.urls import path
from . import views

urlpatterns = [
    path('app-info/', views.app_info, name='app-info'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='api-login'),
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/', views.reset_password, name='reset-password'),
    path('me/', views.me, name='me'),
    path('refresh/', views.refresh_token, name='refresh-token'),
]