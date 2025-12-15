"""
URL patterns for contractors
"""

from django.urls import path
from . import views

app_name = 'contractors'

urlpatterns = [
    path('dashboard/', views.contractor_dashboard, name='dashboard'),
    path('profile/', views.contractor_profile, name='profile'),
    path('services/', views.contractor_services, name='services'),
    path('services/add/', views.add_service, name='add_service'),
    path('services/<uuid:service_id>/edit/', views.edit_service, name='edit_service'),
    path('services/<uuid:service_id>/delete/', views.delete_service, name='delete_service'),
    path('api/subcategories/<uuid:category_id>/', views.get_subcategories, name='get_subcategories'),
]
