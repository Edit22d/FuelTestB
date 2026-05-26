from django.urls import path
from . import views

urlpatterns = [
    path('register/',        views.register,        name='auth-register'),
    path('login/',           views.login,           name='auth-login'),
    path('forgot-password/', views.forgot_password, name='auth-forgot-password'),
    path('reset-password/',  views.reset_password,  name='auth-reset-password'),
    path('me/',              views.me,              name='auth-me'),
    path('token/refresh/',   views.refresh_token,   name='auth-token-refresh'),
]
