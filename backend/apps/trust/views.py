"""
Views for trust scoring and review system
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Avg
from apps.trust.models import TrustMark, Review
from apps.services.models import ContractorService
from apps.contractors.models import ContractorProfile
import logging

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def give_trust_mark(request, service_id):
    """Give a trust mark to a contractor service"""
    try:
        if request.user.user_type != 'customer':
            return JsonResponse({'error': 'Only customers can give trust marks'}, status=403)
        
        service = get_object_or_404(ContractorService, id=service_id)
        
        # Check if already gave trust to this service
        existing_trust = TrustMark.objects.filter(
            customer=request.user,
            contractor_service=service,
            status='active'
        ).first()
        
        if existing_trust:
            return JsonResponse({
                'error': 'You have already trusted this service',
                'existing': True
            }, status=400)
        
        # Create trust mark
        trust_mark = TrustMark.objects.create(
            customer=request.user,
            contractor_service=service,
            is_verified=False,
            review_text=request.POST.get('review_text', ''),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Run fraud detection asynchronously (if Celery is available)
        try:
            from apps.trust.tasks import check_trust_mark_for_fraud
            check_trust_mark_for_fraud.delay(str(trust_mark.id))
        except Exception as e:
            logger.warning(f"Could not queue fraud detection task: {e}")
        
        # Refresh service to get updated trust score
        service.refresh_from_db()
        
        messages.success(request, f'Trust mark given to {service.title}!')
        
        return JsonResponse({
            'success': True,
            'trust_mark_id': str(trust_mark.id),
            'new_trust_score': float(service.trust_score)
        })
        
    except Exception as e:
        logger.error(f"Error giving trust mark: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_trust_mark(request, trust_mark_id):
    """Remove a trust mark"""
    trust_mark = get_object_or_404(TrustMark, id=trust_mark_id, customer=request.user)
    
    trust_mark.status = 'removed'
    trust_mark.save()
    
    messages.success(request, 'Trust mark removed successfully.')
    
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["GET", "POST"])
def add_review(request, service_id):
    """Add detailed review to a contractor service"""
    if request.user.user_type != 'customer':
        messages.error(request, 'Only customers can write reviews.')
        return redirect('home')
    
    service = get_object_or_404(ContractorService, id=service_id)
    
    # Check if trust mark exists
    trust_mark = TrustMark.objects.filter(
        customer=request.user,
        contractor_service=service,
        status='active'
    ).first()
    
    if request.method == 'POST':
        try:
            # Create or update review
            review, created = Review.objects.get_or_create(
                customer=request.user,
                contractor_service=service,
                defaults={'trust_mark': trust_mark}
            )
            
            review.title = request.POST.get('title', '')
            review.text = request.POST.get('text', '')
            review.rating = int(request.POST.get('rating', 5))
            
            # Optional detailed ratings
            quality = request.POST.get('quality_rating')
            if quality:
                review.quality_rating = int(quality)
            
            communication = request.POST.get('communication_rating')
            if communication:
                review.communication_rating = int(communication)
            
            timeliness = request.POST.get('timeliness_rating')
            if timeliness:
                review.timeliness_rating = int(timeliness)
            
            value = request.POST.get('value_rating')
            if value:
                review.value_rating = int(value)
            
            # Project details
            project_cost = request.POST.get('project_cost')
            if project_cost:
                try:
                    review.project_cost = float(project_cost)
                except (ValueError, TypeError):
                    pass
            
            project_duration = request.POST.get('project_duration_days')
            if project_duration:
                try:
                    review.project_duration_days = int(project_duration)
                except (ValueError, TypeError):
                    pass
            
            review.save()
            
            # Analyze sentiment asynchronously (if Celery is available)
            try:
                from apps.trust.tasks import analyze_review_sentiment
                analyze_review_sentiment.delay(str(review.id))
            except Exception as e:
                logger.warning(f"Could not queue sentiment analysis task: {e}")
            
            messages.success(request, 'Review submitted successfully!')
            return redirect('search:contractor_detail', contractor_id=service.contractor.id)
            
        except Exception as e:
            logger.error(f"Error creating review: {e}")
            messages.error(request, f'Error submitting review: {str(e)}')
    
    context = {
        'service': service,
        'contractor': service.contractor,
        'has_trust_mark': trust_mark is not None,
        'existing_review': Review.objects.filter(
            customer=request.user,
            contractor_service=service
        ).first()
    }
    
    return render(request, 'trust/add_review.html', context)


@login_required
def my_trust_marks(request):
    """View all trust marks given by the customer"""
    if request.user.user_type != 'customer':
        messages.error(request, 'This page is only for customers.')
        return redirect('home')
    
    trust_marks = TrustMark.objects.filter(
        customer=request.user
    ).select_related(
        'contractor_service',
        'contractor_service__contractor',
        'contractor_service__contractor__user',
        'contractor_service__category'
    ).prefetch_related('detailed_review').order_by('-created_at')
    
    # Statistics
    stats = {
        'total_trust_marks': trust_marks.filter(status='active').count(),
        'total_reviews': Review.objects.filter(customer=request.user).count(),
        'verified_trust_marks': trust_marks.filter(status='active', is_verified=True).count(),
    }
    
    context = {
        'trust_marks': trust_marks,
        'stats': stats,
    }
    
    return render(request, 'trust/my_trust_marks.html', context)


@login_required
@require_http_methods(["POST"])
def verify_trust_mark(request, trust_mark_id):
    """Upload verification proof for a trust mark"""
    trust_mark = get_object_or_404(TrustMark, id=trust_mark_id, customer=request.user)
    
    if 'verification_proof' in request.FILES:
        trust_mark.verification_proof = request.FILES['verification_proof']
        trust_mark.is_verified = True
        trust_mark.save()
        
        # Recalculate trust score
        trust_mark.contractor_service.trigger_trust_recalculation()
        
        messages.success(request, 'Verification proof uploaded successfully!')
    else:
        messages.error(request, 'Please select a file to upload.')
    
    return redirect('trust:my_trust_marks')


@login_required
@require_http_methods(["POST"])
def mark_review_helpful(request, review_id):
    """Mark a review as helpful"""
    review = get_object_or_404(Review, id=review_id)
    
    helpful = request.POST.get('helpful') == 'true'
    
    if helpful:
        review.helpful_count += 1
    else:
        review.not_helpful_count += 1
    
    review.save()
    
    return JsonResponse({
        'success': True,
        'helpful_count': review.helpful_count,
        'not_helpful_count': review.not_helpful_count
    })


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
