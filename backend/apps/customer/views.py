from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.forms import UserProfileForm
from apps.trust.models import Feedback
from apps.services.models import ServiceCategory


@login_required
def customer_dashboard(request):
    """Customer dashboard view"""
    if request.user.user_type != 'customer':
        messages.error(request, 'Access denied. Customer account required.')
        return redirect('home')

    recent_feedback = (
        Feedback.objects.filter(customer=request.user)
        .select_related(
            'contractor_service',
            'contractor_service__contractor',
            'contractor_service__category',
        )
        .order_by('-updated_at')[:5]
    )

    popular_categories = ServiceCategory.objects.filter(
        is_active=True, parent__isnull=True
    ).order_by('name')[:8]

    context = {
        'user': request.user,
        'recent_feedback': recent_feedback,
        'popular_categories': popular_categories,
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
