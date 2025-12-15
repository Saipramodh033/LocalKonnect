"""
Celery tasks for search ranking
"""

from celery import shared_task
from django.db.models import Max, Min
import logging

logger = logging.getLogger(__name__)


@shared_task
def refresh_ranking_cache():
    """
    Refresh the ranking cache for contractor services.
    Runs every 15 minutes via Celery Beat.
    """
    from apps.services.models import ContractorService
    from apps.search.models import SearchRankingCache
    
    logger.info("Starting ranking cache refresh")
    
    # Get all active services
    services = ContractorService.objects.filter(is_active=True)
    
    if not services.exists():
        logger.info("No active services to rank")
        return {'updated': 0}
    
    # Get max values for normalization
    max_trust = services.aggregate(Max('trust_score'))['trust_score__max'] or 100
    max_exp = services.aggregate(Max('years_of_experience'))['years_of_experience__max'] or 50
    
    updated_count = 0
    
    for service in services:
        # Normalize scores (0-1)
        norm_trust = service.trust_score / max_trust if max_trust > 0 else 0
        norm_exp = service.years_of_experience / max_exp if max_exp > 0 else 0
        
        # Calculate overall rank score
        # Formula: 0.6 * trust + 0.2 * experience + 0.2 * (1 - distance)
        # Distance component will be added in search query
        rank_score = (0.6 * norm_trust) + (0.2 * norm_exp)
        
        # Update or create cache entry
        SearchRankingCache.objects.update_or_create(
            contractor_service=service,
            defaults={
                'normalized_trust_score': norm_trust,
                'normalized_experience': norm_exp,
                'overall_rank_score': rank_score,
            }
        )
        updated_count += 1
    
    logger.info(f"Ranking cache refresh complete: {updated_count} services updated")
    return {'updated': updated_count}
