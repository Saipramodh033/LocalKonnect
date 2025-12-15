"""
Models for search and ranking cache
"""

from django.db import models
from apps.services.models import ContractorService
import uuid


class SearchRankingCache(models.Model):
    """Cache for contractor service rankings"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contractor_service = models.ForeignKey(
        ContractorService,
        on_delete=models.CASCADE,
        related_name='ranking_cache'
    )
    
    # Ranking scores
    normalized_trust_score = models.FloatField(default=0.0)
    normalized_experience = models.FloatField(default=0.0)
    overall_rank_score = models.FloatField(default=0.0)
    
    # Category rankings
    category_rank = models.IntegerField(null=True, blank=True)
    local_rank = models.IntegerField(null=True, blank=True)
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'search_ranking_cache'
        indexes = [
            models.Index(fields=['-overall_rank_score']),
            models.Index(fields=['contractor_service']),
        ]
    
    def __str__(self):
        return f"Ranking for {self.contractor_service} - {self.overall_rank_score}"
