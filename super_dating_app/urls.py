"""
URL configuration for super_dating_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Core URLs
    path('', core_views.home, name='home'),
    path('about/', core_views.about, name='about'),
    path('privacy-policy/', core_views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', core_views.terms_of_service, name='terms_of_service'),
    path('core/', include('core.urls')),
    
    # App-specific URLs
    path('accounts/', include('accounts.urls')),
    path('messaging/', include('messaging.urls')),
    path('video-call/', include('video_call.urls')),
    path('mainstream/', include('mainstream.urls')),
    path('casual/', include('casual.urls')),
    path('sugar/', include('sugar.urls')),
    path('lgbtq/', include('lgbtq.urls')),
    path('religion/', include('religion.urls')),
    path('ethnic/', include('ethnic.urls')),
    path('serious/', include('serious.urls')),
    path('niche/', include('niche.urls')),
    
    # Payment URLs
    path('payments/', include('payments.urls')),
    
    # AllAuth URLs
    path('auth/', include('allauth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Register custom error handlers
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
handler403 = 'core.views.handler403'
handler400 = 'core.views.handler400'
