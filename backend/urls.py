# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from api import dashboard_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('api.urls')),
    
    # Social authentication (Google, Apple)
    path('auth/', include('social_django.urls', namespace='social')),
    
    # Custom Dashboard URLs
    path('dashboard/login/', dashboard_views.dashboard_login, name='dashboard_login'),
    path('dashboard/logout/', dashboard_views.dashboard_logout, name='dashboard_logout'),
    path('dashboard/', include('api.dashboard_urls')),
    
    # Redirect root to dashboard
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
]

# Serve media files in development - CRITICAL for images to work
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)