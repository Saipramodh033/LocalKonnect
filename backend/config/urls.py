"""
URL Configuration for LocalKonnect project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse
from apps.users.template_views import home_view

# Swagger/OpenAPI schema
schema_view = get_schema_view(
    openapi.Info(
        title="LocalKonnect API",
        default_version='v1',
        description="API documentation for Trusted Local Contractor Network",
        terms_of_service="https://www.localkonnect.com/terms/",
        contact=openapi.Contact(email="api@localkonnect.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


def health_check(request):
    """Health check endpoint for container orchestration"""
    return JsonResponse({'status': 'healthy', 'service': 'localkonnect-backend'})


urlpatterns = [
    # Homepage
    path('', home_view, name='home'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('api/health/', health_check, name='health-check'),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # Web interface (template views)
    path('', include('apps.users.template_urls')),  # Auth pages
    path('search/', include('apps.search.urls')),  # Search pages
    path('contractor/', include('apps.contractors.urls')),  # Contractor pages
    path('customer/', include('apps.customer.urls')),  # Customer pages (to be created)
    path('trust/', include('apps.trust.urls')),  # Trust system pages
    
    # API endpoints (users REST API removed)
    path('api/services/', include('apps.services.urls')),
    path('api/admin/', include('apps.admin_panel.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
