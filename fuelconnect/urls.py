from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/v1/auth/', include('authentication.urls')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),

    # 🔥 ADD THIS (fixes /login/ 405 error)
    path('login/', TemplateView.as_view(template_name='authentication/login.html')),
]