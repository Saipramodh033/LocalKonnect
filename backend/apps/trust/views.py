"""
Views for the unified feedback system.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Avg
from apps.trust.models import Feedback
from apps.services.models import ContractorService
import logging

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def submit_feedback(request, service_id):
    """Create or update a single feedback entry for a service."""
    if request.user.user_type != 'customer':
        messages.error(request, 'Only customers can submit feedback.')
        return redirect('home')

    service = get_object_or_404(ContractorService, id=service_id)

    feedback = Feedback.objects.filter(
        customer=request.user,
        contractor_service=service
    ).first()

    if request.method == 'POST':
        try:
            rating_raw = request.POST.get('rating', '')
            rating = int(rating_raw)
            if rating < 1 or rating > 5:
                raise ValueError('Rating must be between 1 and 5')

            feedback, _ = Feedback.objects.get_or_create(
                customer=request.user,
                contractor_service=service,
            )

            feedback.rating = rating
            feedback.text = request.POST.get('text', '').strip() or None
            feedback.is_verified = request.POST.get('is_verified') == 'on'
            feedback.ip_address = get_client_ip(request)
            feedback.user_agent = request.META.get('HTTP_USER_AGENT', '')
            if 'verification_proof' in request.FILES:
                feedback.verification_proof = request.FILES['verification_proof']
                feedback.is_verified = True
            feedback.save()

            service.refresh_from_db(fields=['trust_score'])
            messages.success(request, f'Feedback saved. Updated trust score: {service.trust_score:.1f}')
            return redirect('search:contractor_detail', contractor_id=service.contractor.id)

        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            messages.error(request, f'Could not save feedback: {str(e)}')

    context = {
        'service': service,
        'contractor': service.contractor,
        'feedback': feedback,
    }

    return render(request, 'trust/feedback_form.html', context)


@login_required
def my_feedback(request):
    """View all feedback submitted by the customer."""
    if request.user.user_type != 'customer':
        messages.error(request, 'This page is only for customers.')
        return redirect('home')

    feedback_entries = Feedback.objects.filter(
        customer=request.user
    ).select_related(
        'contractor_service',
        'contractor_service__contractor',
        'contractor_service__contractor__user',
        'contractor_service__category'
    ).order_by('-updated_at')

    stats = {
        'total_feedback': feedback_entries.count(),
        'verified_feedback': feedback_entries.filter(is_verified=True).count(),
        'average_rating': round(feedback_entries.aggregate(avg=Avg('rating'))['avg'] or 0, 2),
    }

    context = {
        'feedback_entries': feedback_entries,
        'stats': stats,
    }

    return render(request, 'trust/my_feedback.html', context)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
