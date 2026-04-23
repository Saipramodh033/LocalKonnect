"""
Views for contractor dashboard and pages
"""

import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .utils import require_contractor_profile
from django.contrib import messages
from django.db.models import Avg, Count
from django.http import JsonResponse
from apps.contractors.models import ContractorProfile
from apps.services.models import ContractorService, ServiceSubcategory
from .forms import ContractorProfileForm, ContractorServiceForm

logger = logging.getLogger(__name__)


@login_required
@require_contractor_profile
def contractor_dashboard(request):
    """Contractor dashboard view"""
    # Ensure user is a contractor
    if request.user.user_type != 'contractor':
        messages.error(request, 'Access denied. Contractor account required.')
        return redirect('home')
    
    # Get or create contractor profile
    profile, created = ContractorProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'office_address': 'Not set',
            'office_location': 'POINT(0 0)'  # Default point, should be updated
        }
    )
    
    # Get contractor services
    services = ContractorService.objects.filter(contractor=profile)
    
    # Calculate statistics
    stats = {
        'total_services': services.count(),
        'avg_trust_score': profile.get_overall_trust_score(),
        'total_jobs_completed': profile.total_jobs_completed,
        'profile_views': profile.profile_views,
        'is_verified': profile.is_identity_verified,
        'verification_status': profile.get_verification_status_display(),
    }
    
    context = {
        'profile': profile,
        'services': services[:5],  # Latest 5 services
        'stats': stats,
    }
    
    return render(request, 'contractor/dashboard.html', context)


@login_required
@require_contractor_profile
def contractor_profile(request):
    """View and edit contractor profile"""
    if request.user.user_type != 'contractor':
        messages.error(request, 'Access denied. Contractor account required.')
        return redirect('home')
    
    profile, created = ContractorProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'office_address': 'Not set',
            'office_location': 'POINT(0 0)'
        }
    )
    
    if request.method == 'POST':
        form = ContractorProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            
            # Update office location if coordinates are provided
            office_lat = request.POST.get('office_latitude')
            office_lng = request.POST.get('office_longitude')
            
            if office_lat and office_lng:
                try:
                    from django.contrib.gis.geos import Point
                    profile.office_location = Point(float(office_lng), float(office_lat), srid=4326)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid coordinates provided: {e}")
            
            profile.save()
            form.save_m2m()  # Save many-to-many relationships if any
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('contractors:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContractorProfileForm(instance=profile)
    
    context = {
        'profile': profile,
        'form': form,
    }
    
    return render(request, 'contractor/profile.html', context)


@login_required
@require_contractor_profile
def contractor_services(request):
    """Manage contractor services"""
    if request.user.user_type != 'contractor':
        messages.error(request, 'Access denied. Contractor account required.')
        return redirect('home')
    
    profile = get_object_or_404(ContractorProfile, user=request.user)
    services = ContractorService.objects.filter(contractor=profile)
    
    context = {
        'profile': profile,
        'services': services,
    }
    
    return render(request, 'contractor/services.html', context)


@login_required
@require_contractor_profile
def add_service(request):
    """Add a new service"""
    if request.user.user_type != 'contractor':
        messages.error(request, 'Access denied. Contractor account required.')
        return redirect('home')
    
    profile = get_object_or_404(ContractorProfile, user=request.user)
    
    if request.method == 'POST':
        form = ContractorServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.contractor = profile
            service.save()
            # Save many-to-many subcategories
            form.save_m2m()
            messages.success(request, 'Service added successfully!')
            return redirect('contractors:services')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContractorServiceForm()
    
    context = {
        'form': form,
        'profile': profile,
    }
    
    return render(request, 'contractor/service_form.html', context)


@login_required
@require_contractor_profile
def edit_service(request, service_id):
    """Edit an existing service"""
    if request.user.user_type != 'contractor':
        messages.error(request, 'Access denied. Contractor account required.')
        return redirect('home')
    
    profile = get_object_or_404(ContractorProfile, user=request.user)
    service = get_object_or_404(ContractorService, id=service_id, contractor=profile)
    
    if request.method == 'POST':
        form = ContractorServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service updated successfully!')
            return redirect('contractors:services')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContractorServiceForm(instance=service)
    
    context = {
        'form': form,
        'service': service,
        'profile': profile,
    }
    
    return render(request, 'contractor/service_form.html', context)


@login_required
@require_contractor_profile
def delete_service(request, service_id):
    """Delete a service"""
    if request.user.user_type != 'contractor':
        messages.error(request, 'Access denied. Contractor account required.')
        return redirect('home')
    
    profile = get_object_or_404(ContractorProfile, user=request.user)
    service = get_object_or_404(ContractorService, id=service_id, contractor=profile)
    
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Service deleted successfully!')
        return redirect('contractors:services')
    
    context = {
        'service': service,
        'profile': profile,
    }
    
    return render(request, 'contractor/service_confirm_delete.html', context)


@login_required
def get_subcategories(request, category_id):
    """API endpoint to get subcategories for a given category"""
    if request.user.user_type != 'contractor':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    subcategories = ServiceSubcategory.objects.filter(
        category_id=category_id,
        is_active=True
    ).values('id', 'name', 'slug')
    
    return JsonResponse({
        'subcategories': list(subcategories)
    })
