"""
Trust Score Calculation Engine

Implements the sophisticated trust scoring algorithm with:
- Diminishing returns for repeat trusts
- Time decay
- Verification bonuses
- Bayesian smoothing
- Experience bonuses
"""

import math
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count, Avg
import logging

logger = logging.getLogger(__name__)


def calculate_trust_weight(trust_number):
    """
    Calculate diminishing weight for repeat trusts from same customer.
    
    Formula: weight_n = max(β^(n-1), min_weight)
    
    Args:
        trust_number: The nth trust from this customer (1-indexed)
    
    Returns:
        float: Weight between min_weight and 1.0
    """
    beta = settings.TRUST_DECAY_FACTOR  # 0.5
    min_weight = settings.TRUST_MIN_WEIGHT  # 0.05
    
    if trust_number <= 0:
        return 1.0
    
    weight = beta ** (trust_number - 1)
    return max(weight, min_weight)


def calculate_time_decay(days_since_trust):
    """
    Calculate time decay factor for trust marks.
    
    Formula: exp(-λ * days)
    
    Args:
        days_since_trust: Number of days since trust was given
    
    Returns:
        float: Decay factor between 0 and 1
    """
    lambda_decay = settings.TRUST_TIME_DECAY_LAMBDA  # 0.01
    return math.exp(-lambda_decay * days_since_trust)


def calculate_trust_contribution(trust_mark):
    """
    Calculate a single trust mark's contribution to overall score.
    
    Formula:
    contribution = weight_n * (1 + α * verified) * reviewer_weight * time_decay
    
    Args:
        trust_mark: TrustMark instance
    
    Returns:
        float: Contribution value
    """
    # Get reviewer weight (1.0 for verified, 0.6 for unverified)
    reviewer_weight = 1.0 if trust_mark.customer.is_verified_reviewer else 0.6
    
    # Verification bonus
    alpha = settings.TRUST_VERIFIED_BONUS  # 0.5
    verified_bonus = 1 + (alpha if trust_mark.is_verified else 0)
    
    # Time decay
    days_old = (timezone.now() - trust_mark.created_at).days
    time_decay = calculate_time_decay(days_old)
    
    # Calculate contribution
    contribution = (
        trust_mark.weight *
        verified_bonus *
        reviewer_weight *
        time_decay
    )
    
    return contribution


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
    1. Sum weighted contributions from all active trust marks
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
            'total_trusts': int,
            'verified_trusts': int
        }
    """
    from apps.trust.models import TrustMark, TrustScoreHistory
    
    # Get all active trust marks
    trust_marks = TrustMark.objects.filter(
        contractor_service=contractor_service,
        status='active'
    ).select_related('customer')
    
    if not trust_marks.exists():
        # No trust marks yet - return base score
        exp_bonus = calculate_experience_bonus(contractor_service.years_of_experience)
        return {
            'final_score': round(exp_bonus, 2),
            'raw_score': 0.0,
            'smoothed_score': 0.0,
            'experience_bonus': round(exp_bonus, 2),
            'total_trusts': 0,
            'verified_trusts': 0
        }
    
    # Calculate raw score (sum of contributions)
    raw_score = 0.0
    verified_count = 0
    
    for trust_mark in trust_marks:
        contribution = calculate_trust_contribution(trust_mark)
        raw_score += contribution
        
        # Update trust mark contribution for transparency
        if trust_mark.contribution_score != contribution:
            trust_mark.contribution_score = contribution
            trust_mark.save(update_fields=['contribution_score'])
        
        if trust_mark.is_verified:
            verified_count += 1
    
    # Apply Bayesian smoothing
    smoothed_score = apply_bayesian_smoothing(raw_score)
    
    # Calculate experience bonus
    experience_bonus = calculate_experience_bonus(
        contractor_service.years_of_experience
    )
    
    # Calculate final score
    final_score = min((smoothed_score * 100) + experience_bonus, 100)
    
    # Save to history
    TrustScoreHistory.objects.create(
        contractor_service=contractor_service,
        trust_score=final_score,
        total_trust_marks=trust_marks.count(),
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
        'total_trusts': trust_marks.count(),
        'verified_trusts': verified_count
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
    
    # Update the service record
    contractor_service.trust_score = result['final_score']
    contractor_service.total_trust_marks = result['total_trusts']
    contractor_service.verified_trust_marks = result['verified_trusts']
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
