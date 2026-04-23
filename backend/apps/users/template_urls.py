"""
Template view URLs for user authentication
"""

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import template_views

app_name = 'users'

urlpatterns = [
    # Template views (for web interface)
    path('register/', template_views.register_view, name='register'),
    path('login/', template_views.login_view, name='login'),
    path('logout/', template_views.logout_view, name='logout'),
    path('profile/', template_views.profile_view, name='profile'),
    path('settings/', template_views.settings_view, name='settings'),
    
    # Settings actions
    path('settings/update-profile/', template_views.update_profile_view, name='update_profile'),
    path('settings/update-address/', template_views.update_address_view, name='update_address'),
    path('settings/change-password/', template_views.change_password_view, name='change_password'),
    
    # Password Reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='auth/password_reset_form.html',
             email_template_name='auth/password_reset_email.html',
             subject_template_name='auth/password_reset_subject.txt',
             success_url=reverse_lazy('users:password_reset_done')
         ),
         name='password_reset'),
         
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='auth/password_reset_done.html'
         ), 
         name='password_reset_done'),
         
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset_confirm.html',
             success_url=reverse_lazy('users:password_reset_complete')
         ), 
         name='password_reset_confirm'),
         
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]
