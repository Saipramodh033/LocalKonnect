"""
Template view URLs for user authentication
"""

from django.urls import path
from . import template_views

app_name = 'users'

urlpatterns = [
    # Template views (for web interface)
    path('register/', template_views.register_view, name='register'),
    path('login/', template_views.login_view, name='login'),
    path('logout/', template_views.logout_view, name='logout'),
    path('profile/', template_views.profile_view, name='profile'),
    path('settings/', template_views.settings_view, name='settings'),
    path('password-reset/', template_views.password_reset_view, name='password_reset'),
    
    # Settings actions
    path('settings/update-profile/', template_views.update_profile_view, name='update_profile'),
    path('settings/update-address/', template_views.update_address_view, name='update_address'),
    path('settings/change-password/', template_views.change_password_view, name='change_password'),
    path('settings/update-notifications/', template_views.update_notifications_view, name='update_notifications'),
]
