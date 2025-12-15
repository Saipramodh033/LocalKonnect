"""
Views for customer dashboard and pages
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.forms import UserProfileForm


@login_required
def customer_dashboard(request):
    """Customer dashboard view"""
    # Ensure user is a customer
    if request.user.user_type != 'customer':
        messages.error(request, 'Access denied. Customer account required.')
        return redirect('home')
    
    context = {
        'user': request.user,
    }
    
    return render(request, 'customer/dashboard.html', context)


@login_required
def customer_profile(request):
    """View and edit customer profile"""
    if request.user.user_type != 'customer':
        messages.error(request, 'Access denied. Customer account required.')
        return redirect('home')
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('customer:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'user': request.user,
        'form': form,
    }
    
    return render(request, 'customer/profile.html', context)


@login_required
def customer_saved_contractors(request):
    """View saved/favorite contractors"""
    if request.user.user_type != 'customer':
        messages.error(request, 'Access denied. Customer account required.')
        return redirect('home')
    
    context = {
        'user': request.user,
    }
    
    return render(request, 'customer/saved_contractors.html', context)
