"""
Celery tasks for trust score calculations and fraud detection
"""

from celery import shared_task
from django.utils import timezone
from apps.trust.utils import update_service_trust_score, batch_update_all_trust_scores
from apps.trust.models import TrustMark, FraudPattern
from apps.services.models import ContractorService
import logging

logger = logging.getLogger(__name__)


@shared_task
def recalculate_service_trust_score(service_id):
    """
    Recalculate trust score for a single contractor service.
    Triggered when a new trust mark is added.
    """
    try:
        service = ContractorService.objects.get(id=service_id)
        result = update_service_trust_score(service)
        logger.info(f"Updated trust score for {service}: {result['final_score']}")
        return result
    except ContractorService.DoesNotExist:
        logger.error(f"Service {service_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error recalculating trust score: {e}")
        raise


@shared_task
def batch_recompute_trust_scores():
    """
    Nightly batch job to recalculate all trust scores.
    Scheduled by Celery Beat.
    """
    logger.info("Starting batch trust score recomputation")
    result = batch_update_all_trust_scores()
    logger.info(f"Batch recomputation complete: {result}")
    return result


@shared_task
def scan_fraud_patterns():
    """
    Scan for fraud patterns across trust marks and reviews.
    Runs every 30 minutes via Celery Beat.
    """
    logger.info("Starting fraud pattern scan")
    
    from apps.trust.fraud_detection import (
        detect_rapid_trust_bursts,
        detect_identical_reviews,
        detect_ip_clustering,
        detect_coordinated_attacks
    )
    
    patterns_found = 0
    
    try:
        # Detect rapid trust bursts
        bursts = detect_rapid_trust_bursts()
        patterns_found += len(bursts)
        
        # Detect identical review text
        duplicates = detect_identical_reviews()
        patterns_found += len(duplicates)
        
        # Detect IP clustering
        clusters = detect_ip_clustering()
        patterns_found += len(clusters)
        
        # Detect coordinated attacks
        attacks = detect_coordinated_attacks()
        patterns_found += len(attacks)
        
        logger.info(f"Fraud scan complete. Found {patterns_found} patterns.")
        
        return {
            'patterns_found': patterns_found,
            'bursts': len(bursts),
            'duplicates': len(duplicates),
            'clusters': len(clusters),
            'attacks': len(attacks)
        }
    
    except Exception as e:
        logger.error(f"Error in fraud pattern scan: {e}")
        raise


@shared_task
def analyze_review_sentiment(review_id):
    """
    Analyze sentiment of a review using AI.
    Triggered when a review is submitted.
    """
    try:
        from apps.trust.models import Review
        from apps.ai.gemini_client import analyze_sentiment
        
        review = Review.objects.get(id=review_id)
        
        # Analyze sentiment
        sentiment = analyze_sentiment(review.text)
        review.sentiment_score = sentiment.get('score', 0.0)
        review.ai_summary = sentiment.get('summary', '')
        review.key_themes = sentiment.get('themes', [])
        review.save(update_fields=['sentiment_score', 'ai_summary', 'key_themes'])
        
        logger.info(f"Analyzed sentiment for review {review_id}: {sentiment['score']}")
        return sentiment
    
    except Exception as e:
        logger.error(f"Error analyzing review sentiment: {e}")
        raise


@shared_task
def check_trust_mark_for_fraud(trust_mark_id):
    """
    Check a trust mark for fraud indicators using AI.
    Triggered when a trust mark is created.
    """
    try:
        from apps.ai.gemini_client import check_fraud_likelihood
        
        trust_mark = TrustMark.objects.get(id=trust_mark_id)
        
        # Check fraud likelihood
        fraud_result = check_fraud_likelihood(trust_mark)
        
        if fraud_result['confidence'] > 0.7:
            trust_mark.is_flagged_as_fraud = True
            trust_mark.fraud_confidence = fraud_result['confidence']
            trust_mark.flag_reason = fraud_result.get('reason', 'High fraud likelihood detected')
            trust_mark.status = 'under_review'
            trust_mark.save()
            
            # Create fraud pattern record
            FraudPattern.objects.create(
                pattern_type='review_manipulation',
                severity='high' if fraud_result['confidence'] > 0.9 else 'medium',
                description=fraud_result.get('reason', 'Suspicious trust mark detected'),
                confidence_score=fraud_result['confidence'],
                evidence=fraud_result.get('evidence', {})
            ).affected_trust_marks.add(trust_mark)
            
            logger.warning(f"Trust mark {trust_mark_id} flagged as potential fraud")
        
        return fraud_result
    
    except Exception as e:
        logger.error(f"Error checking trust mark for fraud: {e}")
        raise
