from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import User
from apps.services.models import ContractorService
import uuid


class Feedback(models.Model):
    """Single feedback record per customer and contractor service."""

    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedback_entries'
    )
    contractor_service = models.ForeignKey(
        ContractorService,
        on_delete=models.CASCADE,
        related_name='feedback_entries'
    )

    rating = models.IntegerField(choices=RATING_CHOICES)
    text = models.TextField(blank=True, null=True, max_length=1000)
    is_verified = models.BooleanField(default=False)
    verification_proof = models.FileField(
        upload_to='feedback_verification/',
        null=True,
        blank=True,
        help_text="Optional proof of verified job completion"
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'feedback'
        unique_together = ['customer', 'contractor_service']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['contractor_service', '-updated_at'], name='feedback_contrac_36fd47_idx'),
            models.Index(fields=['customer', '-created_at'], name='feedback_custome_88c0ba_idx'),
            models.Index(fields=['rating'], name='feedback_rating_d746a3_idx'),
            models.Index(fields=['is_verified'], name='feedback_is_ver_2b64de_idx'),
        ]

    def __str__(self):
        return f"Feedback({self.rating}) by {self.customer.email}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.contractor_service.trigger_trust_recalculation()


class TrustScoreHistory(models.Model):
    """Track historical trust scores for analytics."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contractor_service = models.ForeignKey(
        ContractorService,
        on_delete=models.CASCADE,
        related_name='trust_score_history'
    )
    trust_score = models.FloatField()
    total_trust_marks = models.IntegerField()
    verified_trust_marks = models.IntegerField()
    
    # Score components (for transparency)
    raw_score = models.FloatField()
    smoothed_score = models.FloatField()
    experience_bonus = models.FloatField()
    
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trust_score_history'
        ordering = ['-calculated_at']
        indexes = [
            models.Index(fields=['contractor_service', '-calculated_at']),
        ]
    
    def __str__(self):
        return f"{self.contractor_service} - {self.trust_score} at {self.calculated_at}"
