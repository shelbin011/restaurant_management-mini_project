"""restaurant URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views as project_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', project_views.unified_login, name='login'),
    path('logout/', project_views.unified_logout, name='logout'),
    path('admin_app/', include(('admin_app.urls', 'admin_app'), namespace='admin_app')),
    path('', include(('customer_app.urls', 'customer_app'), namespace='customer_app')),
    path('waiter_app/', include(('waiter_app.urls', 'waiter_app'), namespace='waiter_app')),
    path('debug/media-check/', project_views.debug_media_check, name='debug_media_check'),
]

# Serve media files in development or when explicitly requested via env var
import os

if settings.DEBUG or os.environ.get('SERVE_MEDIA') == '1':
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)