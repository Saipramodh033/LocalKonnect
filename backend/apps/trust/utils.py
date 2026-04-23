"""
Trust Score Calculation Engine

Implements the sophisticated trust scoring algorithm with:
- Rating-weighted contributions
- Verification bonuses
- Bayesian smoothing
- Experience bonuses
"""

import math
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def calculate_feedback_contribution(feedback):
    """
    Calculate a single feedback contribution to overall trust score.

    Args:
        feedback: Feedback instance

    Returns:
        float: Contribution value
    """
    # Use the stored reviewer_weight field; verified reviewers are capped at 1.0.
    customer = feedback.customer
    if customer.is_verified_reviewer:
        reviewer_weight = 1.0
    else:
        reviewer_weight = float(customer.reviewer_weight)  # default 0.6

    alpha = settings.TRUST_VERIFIED_BONUS  # 0.5
    verified_bonus = 1 + (alpha if feedback.is_verified else 0)
    rating_factor = feedback.rating / 5.0

    return rating_factor * verified_bonus * reviewer_weight



def calculate_experience_bonus(years_of_experience):
    """
    Calculate experience bonus points.
    
    Formula: min(log(1 + years_exp) * 5, 15)
    
    Args:
        years_of_experience: Years of experience in service
    
    Returns:
        float: Bonus points (0-15)
    """
    max_bonus = settings.TRUST_MAX_EXPERIENCE_BONUS  # 15
    
    if years_of_experience <= 0:
        return 0.0
    
    bonus = math.log(1 + years_of_experience) * 5
    return min(bonus, max_bonus)


def apply_bayesian_smoothing(raw_score, smoothing_k=None):
    """
    Apply Bayesian smoothing for stability with low sample sizes.
    
    Formula: S_raw / (S_raw + k)
    
    Args:
        raw_score: Raw trust score sum
        smoothing_k: Smoothing constant (default from settings)
    
    Returns:
        float: Smoothed value between 0 and 1
    """
    if smoothing_k is None:
        smoothing_k = settings.TRUST_SMOOTHING_K  # 5
    
    return raw_score / (raw_score + smoothing_k)


def calculate_service_trust_score(contractor_service):
    """
    Calculate complete trust score for a contractor service.
    
    Complete algorithm:
    1. Sum weighted contributions from all feedback entries
    2. Apply Bayesian smoothing
    3. Add experience bonus
    4. Cap at 100
    
    Args:
        contractor_service: ContractorService instance
    
    Returns:
        dict: {
            'final_score': float (0-100),
            'raw_score': float,
            'smoothed_score': float,
            'experience_bonus': float,
            'total_feedbacks': int,
            'verified_feedbacks': int
        }
    """
    from apps.trust.models import Feedback, TrustScoreHistory

    feedback_entries = Feedback.objects.filter(
        contractor_service=contractor_service
    ).select_related('customer')

    if not feedback_entries.exists():
        exp_bonus = calculate_experience_bonus(contractor_service.years_of_experience)
        return {
            'final_score': round(exp_bonus, 2),
            'raw_score': 0.0,
            'smoothed_score': 0.0,
            'experience_bonus': round(exp_bonus, 2),
            'total_feedbacks': 0,
            'verified_feedbacks': 0
        }

    raw_score = 0.0
    verified_count = 0

    for feedback in feedback_entries:
        contribution = calculate_feedback_contribution(feedback)
        raw_score += contribution

        if feedback.is_verified:
            verified_count += 1

    smoothed_score = apply_bayesian_smoothing(raw_score)

    experience_bonus = calculate_experience_bonus(
        contractor_service.years_of_experience
    )

    final_score = min((smoothed_score * 100) + experience_bonus, 100)

    TrustScoreHistory.objects.create(
        contractor_service=contractor_service,
        trust_score=final_score,
        total_trust_marks=feedback_entries.count(),
        verified_trust_marks=verified_count,
        raw_score=raw_score,
        smoothed_score=smoothed_score,
        experience_bonus=experience_bonus
    )

    logger.info(
        f"Calculated trust score for {contractor_service}: "
        f"Final={final_score:.2f}, Raw={raw_score:.2f}, "
        f"Smoothed={smoothed_score:.2f}, ExpBonus={experience_bonus:.2f}"
    )

    return {
        'final_score': round(final_score, 2),
        'raw_score': round(raw_score, 2),
        'smoothed_score': round(smoothed_score, 2),
        'experience_bonus': round(experience_bonus, 2),
        'total_feedbacks': feedback_entries.count(),
        'verified_feedbacks': verified_count
    }


def update_service_trust_score(contractor_service):
    """
    Update the trust score stored in database for a service.
    
    Args:
        contractor_service: ContractorService instance
    
    Returns:
        dict: Trust score calculation results
    """
    result = calculate_service_trust_score(contractor_service)

    contractor_service.trust_score = result['final_score']
    contractor_service.total_trust_marks = result['total_feedbacks']
    contractor_service.verified_trust_marks = result['verified_feedbacks']
    contractor_service.trust_score_last_calculated = timezone.now()
    contractor_service.save(update_fields=[
        'trust_score',
        'total_trust_marks',
        'verified_trust_marks',
        'trust_score_last_calculated'
    ])

    return result


def batch_update_all_trust_scores():
    """
    Update trust scores for all active contractor services.
    Used by nightly Celery task.
    
    Returns:
        dict: Summary of updates
    """
    from apps.services.models import ContractorService
    
    services = ContractorService.objects.filter(is_active=True)
    total = services.count()
    updated = 0
    errors = 0
    
    logger.info(f"Starting batch trust score update for {total} services")
    
    for service in services:
        try:
            update_service_trust_score(service)
            updated += 1
        except Exception as e:
            logger.error(f"Error updating trust score for {service}: {e}")
            errors += 1
    
    logger.info(
        f"Batch update complete: {updated} updated, {errors} errors"
    )
    
    return {
        'total': total,
        'updated': updated,
        'errors': errors
    }
