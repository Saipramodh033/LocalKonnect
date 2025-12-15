"""
Views for search and discovery functionality
"""

from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from apps.contractors.models import ContractorProfile
from apps.services.models import ContractorService, ServiceCategory
import json


@cache_page(60)  # Cache search page for 60 seconds
def search_results(request):
    """Search results page for contractors"""
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    category_slug = request.GET.get('category', '')
    min_trust = int(request.GET.get('min_trust', '0'))
    min_experience = int(request.GET.get('min_experience', '0'))
    verified_only = request.GET.get('verified_only', False)
    
    # Get all service categories for the filter
    categories = ServiceCategory.objects.filter(is_active=True, parent__isnull=True).order_by('name')
    
    # Start with all active services
    services = ContractorService.objects.filter(
        contractor__is_accepting_jobs=True
    ).select_related('contractor', 'contractor__user', 'category')
    
    # Filter by verification status
    if verified_only:
        services = services.filter(contractor__is_identity_verified=True)
    
    # Filter by service category if provided
    if category_slug:
        services = services.filter(category__slug=category_slug)
    
    # Filter by trust score
    if min_trust > 0:
        services = services.filter(trust_score__gte=min_trust)
    
    # Filter by experience
    if min_experience > 0:
        services = services.filter(years_of_experience__gte=min_experience)
    
    # Filter by search query
    if query:
        services = services.filter(
            Q(contractor__business_name__icontains=query) |
            Q(contractor__user__first_name__icontains=query) |
            Q(contractor__user__last_name__icontains=query) |
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    # Get distinct services
    services = services.distinct()[:50]  # Limit to 50 results
    
    # Prepare contractors data for map
    contractors_data = []
    for service in services:
        if service.contractor.office_location:
            contractors_data.append({
                'id': str(service.contractor.id),
                'name': service.contractor.business_name or service.contractor.user.get_full_name(),
                'service': service.category.name,
                'trust_score': float(service.trust_score),
                'lat': service.contractor.office_location.y if service.contractor.office_location else 0,
                'lng': service.contractor.office_location.x if service.contractor.office_location else 0,
                'address': service.contractor.office_address,
            })
    
    context = {
        'query': query,
        'location': location,
        'categories': categories,
        'contractors': services,
        'contractors_json': json.dumps(contractors_data),
        'total_results': services.count(),
    }
    
    # If HTMX request, return only the results partial
    if request.headers.get('HX-Request'):
        return render(request, 'search/results_partial.html', context)
    
    return render(request, 'search/search.html', context)


@cache_page(120)  # Cache contractor detail for 2 minutes
def contractor_detail(request, contractor_id):
    """Contractor detail page"""
    contractor = get_object_or_404(
        ContractorProfile.objects.select_related('user'),
        id=contractor_id
    )
    services = ContractorService.objects.filter(
        contractor=contractor
    ).select_related('category')
    
    context = {
        'contractor': contractor,
        'services': services,
    }
    
    return render(request, 'search/contractor_detail.html', context)
