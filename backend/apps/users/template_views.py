"""
Template views for LocalKonnect frontend
Handles server-rendered pages with HTMX support
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .models import User
from .forms import UserRegistrationForm, UserLoginForm
import logging

logger = logging.getLogger(__name__)


def home_view(request):
    """Homepage view"""
    return render(request, 'base/home.html')


@require_http_methods(["GET", "POST"])
def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            
            # Auto-login after registration
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Redirect based on user type
            if user.user_type == 'contractor':
                return redirect('contractors:dashboard')
            else:
                return redirect('customer:dashboard')
        else:
            # If HTMX request, return form with errors
            if request.headers.get('HX-Request'):
                return render(request, 'auth/register.html', {'form': form})
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'auth/register.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            expected_user_type = request.POST.get('expected_user_type', '')
            
            # Authenticate user
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                # Validate user type matches selection
                if expected_user_type and user.user_type != expected_user_type:
                    type_names = {'customer': 'Customer', 'contractor': 'Contractor'}
                    messages.error(request, f'This account is registered as a {type_names.get(user.user_type, user.user_type)}. Please select the correct account type.')
                    return render(request, 'auth/login.html', {'form': form})
                
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                
                # Redirect to next parameter if provided
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                # Redirect based on user type
                if user.user_type == 'contractor':
                    return redirect('contractors:dashboard')
                elif user.user_type == 'customer':
                    return redirect('customer:dashboard')
                else:
                    # For admin or other user types
                    return redirect('home')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            if request.headers.get('HX-Request'):
                return render(request, 'auth/login.html', {'form': form})
    else:
        form = UserLoginForm()
    
    return render(request, 'auth/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'auth/profile.html', {
        'user': request.user
    })


@login_required
def settings_view(request):
    """User settings view"""
    return render(request, 'auth/settings.html', {
        'user': request.user
    })


@login_required
@require_http_methods(["POST"])
def update_profile_view(request):
    """Update user profile information"""
    user = request.user
    
    # Handle avatar upload
    if 'avatar' in request.FILES:
        user.avatar = request.FILES['avatar']
    
    # Update basic fields
    user.first_name = request.POST.get('first_name', user.first_name)
    user.last_name = request.POST.get('last_name', user.last_name)
    user.phone_number = request.POST.get('phone_number', user.phone_number)
    user.bio = request.POST.get('bio', user.bio)
    
    # Validate and update email
    new_email = request.POST.get('email')
    if new_email and new_email != user.email:
        if User.objects.filter(email=new_email).exclude(id=user.id).exists():
            messages.error(request, 'This email is already in use.')
            return redirect('users:settings')
        user.email = new_email
        user.is_email_verified = False  # Require re-verification
    
    user.save()
    messages.success(request, 'Profile updated successfully!')
    return redirect('users:settings')


@login_required
@require_http_methods(["POST"])
def update_address_view(request):
    """Update user address information"""
    user = request.user
    
    user.address = request.POST.get('address', user.address)
    user.city = request.POST.get('city', user.city)
    user.state = request.POST.get('state', user.state)
    user.postal_code = request.POST.get('postal_code', user.postal_code)
    user.country = request.POST.get('country', user.country)
    
    user.save()
    messages.success(request, 'Address updated successfully!')
    return redirect('users:settings')


@login_required
@require_http_methods(["POST"])
def change_password_view(request):
    """Change user password"""
    current_password = request.POST.get('current_password')
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')
    
    # Verify current password
    if not request.user.check_password(current_password):
        messages.error(request, 'Current password is incorrect.')
        return redirect('users:settings')
    
    # Validate new password
    if new_password != confirm_password:
        messages.error(request, 'New passwords do not match.')
        return redirect('users:settings')
    
    if len(new_password) < 8:
        messages.error(request, 'Password must be at least 8 characters long.')
        return redirect('users:settings')
    
    # Update password
    request.user.set_password(new_password)
    request.user.save()
    
    # Re-authenticate to maintain session
    login(request, request.user, backend='django.contrib.auth.backends.ModelBackend')
    
    messages.success(request, 'Password changed successfully!')
    return redirect('users:settings')

