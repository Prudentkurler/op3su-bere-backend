"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def api_status(request):
    """Simple API status endpoint for root path"""
    return JsonResponse({
        'status': 'operational',
        'message': 'Op3su Backend API is running successfully on Azure!',
        'endpoints': {
            'admin': '/admin/',
            'weather_analysis': '/api/weather/',
            'geospatial_segmentation': '/api/geospatial-segmentation/',
            'user_auth': '/api/auth/'
        },
        'version': '1.0.0'
    })

urlpatterns = [
    path('', api_status, name='api_status'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/', include('api.urls')),
]
