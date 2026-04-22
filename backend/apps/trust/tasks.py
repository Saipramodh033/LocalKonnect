"""
Celery tasks for trust score recalculation.
"""

from celery import shared_task
from apps.trust.utils import update_service_trust_score, batch_update_all_trust_scores
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
