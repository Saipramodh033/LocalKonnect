"""
Views for search and discovery functionality
"""

from django.shortcuts import render, get_object_or_404
from django.db.models import Q, F, FloatField, ExpressionWrapper, Value, Avg, Count
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from apps.contractors.models import ContractorProfile
from apps.services.models import ContractorService, ServiceCategory
from apps.trust.models import Feedback
import json


def _parse_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_location(location_text):
    """Parse 'lat,lng' into a Point. Returns None on invalid input."""
    if not location_text:
        return None

    raw = location_text.strip()
    parts = [p.strip() for p in raw.split(',')]
    if len(parts) != 2:
        return None

    try:
        lat = float(parts[0])
        lng = float(parts[1])
    except ValueError:
        return None

    if lat < -90 or lat > 90 or lng < -180 or lng > 180:
        return None

    return Point(lng, lat, srid=4326)


def search_results(request):
    """Search results page for contractors"""
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    category_slug = request.GET.get('category', '')
    min_trust = _parse_int(request.GET.get('min_trust', '0'), default=0)
    min_experience = _parse_int(request.GET.get('min_experience', '0'), default=0)
    verified_only = request.GET.get('verified_only') in ('1', 'true', 'on', True)
    
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

    search_point = _parse_location(location)
    using_profile_location = False
    if not search_point and request.user.is_authenticated and getattr(request.user, 'location', None):
        search_point = request.user.location
        using_profile_location = True

    if search_point:
        services = services.filter(contractor__office_location__isnull=False).annotate(
            distance_m=Distance('contractor__office_location', search_point)
        ).annotate(
            distance_km=ExpressionWrapper(F('distance_m') / Value(1000.0), output_field=FloatField()),
            trust_component=ExpressionWrapper(F('trust_score') / Value(100.0), output_field=FloatField()),
            distance_component=ExpressionWrapper(Value(1.0) / (Value(1.0) + F('distance_km')), output_field=FloatField()),
        ).filter(
            distance_km__lte=F('contractor__service_radius_km')
        ).annotate(
            rank_score=ExpressionWrapper(
                (F('trust_component') * Value(0.65)) + (F('distance_component') * Value(0.35)),
                output_field=FloatField(),
            )
        ).order_by('-rank_score', 'distance_km', '-trust_score', '-created_at')
    else:
        services = services.annotate(
            distance_km=Value(None, output_field=FloatField())
        ).order_by('-trust_score', '-created_at')

    services = services.distinct()[:50]
    
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
                'distance_km': float(service.distance_km) if service.distance_km is not None else None,
            })
    
    context = {
        'query': query,
        'location': location,
            'using_profile_location': using_profile_location,
            'location_invalid': bool(location and not _parse_location(location)),
        'categories': categories,
        'contractors': services,
        'contractors_json': json.dumps(contractors_data),
        'total_results': services.count(),
    }
    
    # If HTMX request, return only the results partial
    if request.headers.get('HX-Request'):
        return render(request, 'search/results_partial.html', context)
    
    return render(request, 'search/search.html', context)


def contractor_detail(request, contractor_id):
    """Contractor detail page"""
    contractor = get_object_or_404(
        ContractorProfile.objects.select_related('user'),
        id=contractor_id
    )
    services = ContractorService.objects.filter(
        contractor=contractor
    ).select_related('category').annotate(
        average_rating=Avg('feedback_entries__rating'),
        feedback_count=Count('feedback_entries')
    )

    if request.user.is_authenticated and request.user.user_type == 'customer':
        feedback_map = {
            str(item.contractor_service_id): item
            for item in Feedback.objects.filter(
                customer=request.user,
                contractor_service__in=services,
            )
        }
        for service in services:
            service.current_user_feedback = feedback_map.get(str(service.id))
    
    context = {
        'contractor': contractor,
        'services': services,
    }
    
    return render(request, 'search/contractor_detail.html', context)
