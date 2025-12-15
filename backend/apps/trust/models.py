from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.users.models import User
from apps.services.models import ContractorService
import uuid


class TrustMark(models.Model):
    """Trust marks given by customers to contractor services"""
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('flagged', 'Flagged'),
        ('disputed', 'Disputed'),
        ('removed', 'Removed'),
        ('under_review', 'Under Review'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_trust_marks'
    )
    contractor_service = models.ForeignKey(
        ContractorService,
        on_delete=models.CASCADE,
        related_name='trust_marks'
    )
    
    # Trust details
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether this trust has job proof/verification"
    )
    verification_proof = models.FileField(
        upload_to='trust_verification/',
        null=True,
        blank=True,
        help_text="Job completion proof (photos, invoice, etc.)"
    )
    
    # Optional review text
    review_text = models.TextField(
        blank=True,
        null=True,
        max_length=1000,
        help_text="Optional short review"
    )
    
    # Calculated weight for this trust mark
    weight = models.FloatField(
        default=1.0,
        help_text="Diminishing weight based on repeat trusts"
    )
    contribution_score = models.FloatField(
        default=0.0,
        help_text="Calculated contribution to overall trust score"
    )
    
    # Tracking
    trust_number_for_customer = models.IntegerField(
        default=1,
        help_text="Which number trust this is from same customer to same service"
    )
    
    # Moderation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_flagged_as_fraud = models.BooleanField(default=False)
    fraud_confidence = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="AI-calculated fraud likelihood (0-1)"
    )
    flag_reason = models.TextField(blank=True, null=True)
    
    # Admin actions
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_trust_marks'
    )
    admin_notes = models.TextField(blank=True, null=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    device_fingerprint = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trust_marks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contractor_service', 'status', '-created_at']),
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['is_flagged_as_fraud']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Trust from {self.customer.email} to {self.contractor_service}"
    
    def save(self, *args, **kwargs):
        # Calculate trust number for this customer-service pair
        if not self.pk:
            previous_count = TrustMark.objects.filter(
                customer=self.customer,
                contractor_service=self.contractor_service,
                status='active'
            ).count()
            self.trust_number_for_customer = previous_count + 1
            
            # Calculate initial weight using diminishing returns formula
            from apps.trust.utils import calculate_trust_weight
            self.weight = calculate_trust_weight(self.trust_number_for_customer)
        
        super().save(*args, **kwargs)
        
        # Trigger trust score recalculation
        if self.status == 'active':
            self.contractor_service.trigger_trust_recalculation()


class Review(models.Model):
    """Detailed reviews for contractor services (optional, separate from trust marks)"""
    
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trust_mark = models.OneToOneField(
        TrustMark,
        on_delete=models.CASCADE,
        related_name='detailed_review',
        null=True,
        blank=True
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    contractor_service = models.ForeignKey(
        ContractorService,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    # Review content
    title = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField()
    rating = models.IntegerField(choices=RATING_CHOICES)
    
    # Detailed ratings
    quality_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    communication_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    timeliness_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    value_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    
    # Project details
    project_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    project_duration_days = models.IntegerField(null=True, blank=True)
    
    # AI analysis
    sentiment_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)],
        help_text="AI-analyzed sentiment (-1 to 1)"
    )
    ai_summary = models.TextField(blank=True, null=True)
    key_themes = models.JSONField(default=list, blank=True)
    
    # Helpfulness
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    
    # Moderation
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.TextField(blank=True, null=True)
    is_verified_purchase = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contractor_service', '-created_at']),
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"Review by {self.customer.email} - {self.rating}★"


class FraudPattern(models.Model):
    """Detected fraud patterns for monitoring and prevention"""
    
    PATTERN_TYPES = (
        ('rapid_burst', 'Rapid Trust Burst'),
        ('identical_text', 'Identical Review Text'),
        ('ip_cluster', 'IP Address Clustering'),
        ('coordinated_attack', 'Coordinated Attack'),
        ('fake_accounts', 'Fake Account Network'),
        ('review_manipulation', 'Review Manipulation'),
    )
    
    SEVERITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pattern_type = models.CharField(max_length=50, choices=PATTERN_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    
    # Affected entities
    affected_contractor_service = models.ForeignKey(
        ContractorService,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fraud_patterns'
    )
    affected_users = models.ManyToManyField(User, related_name='fraud_patterns')
    affected_trust_marks = models.ManyToManyField(TrustMark, related_name='fraud_patterns')
    
    # Pattern details
    description = models.TextField()
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="AI confidence in fraud detection (0-1)"
    )
    evidence = models.JSONField(default=dict)
    
    # Actions taken
    is_resolved = models.BooleanField(default=False)
    action_taken = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_fraud_patterns'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fraud_patterns'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['pattern_type', '-detected_at']),
            models.Index(fields=['severity', 'is_resolved']),
            models.Index(fields=['-detected_at']),
        ]
    
    def __str__(self):
        return f"{self.pattern_type} - {self.severity} ({self.detected_at})"


class TrustScoreHistory(models.Model):
    """Track historical trust scores for analytics"""
    
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
