"""
Celery tasks for contractor management
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_verifications():
    """
    Clean up expired verification documents.
    Runs daily via Celery Beat.
    """
    from apps.contractors.models import ContractorProfile
    
    expired_count = 0
    threshold_date = timezone.now() - timedelta(days=365)  # 1 year expiry
    
    expired_profiles = ContractorProfile.objects.filter(
        verification_status='verified',
        verification_date__lt=threshold_date
    )
    
    for profile in expired_profiles:
        profile.verification_status = 'expired'
        profile.save(update_fields=['verification_status'])
        expired_count += 1
        logger.info(f"Marked verification as expired for {profile.business_name}")
    
    logger.info(f"Cleaned up {expired_count} expired verifications")
    return {'expired_count': expired_count}
