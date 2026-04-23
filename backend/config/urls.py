"""
URL Configuration for LocalKonnect project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from apps.users.template_views import home_view


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

    # Web interface (template views)
    path('', include('apps.users.template_urls')),      # Auth pages
    path('search/', include('apps.search.urls')),        # Search + contractor detail
    path('contractor/', include('apps.contractors.urls')),  # Contractor dashboard/CRUD
    path('customer/', include('apps.customer.urls')),    # Customer dashboard/profile
    path('trust/', include('apps.trust.urls')),          # Feedback submission
    
    # Allauth
    path('accounts/', include('allauth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
