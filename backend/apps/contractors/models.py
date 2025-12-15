from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import User
import uuid


class ContractorProfile(models.Model):
    """Extended profile for contractor users"""
    
    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='contractor_profile')
    
    # Business information
    business_name = models.CharField(max_length=255, blank=True, null=True)
    business_registration_number = models.CharField(max_length=100, blank=True, null=True)
    business_license = models.FileField(upload_to='contractor_licenses/', null=True, blank=True)
    
    # Office/Work location
    office_location = gis_models.PointField(geography=True, srid=4326)
    office_address = models.CharField(max_length=500)
    service_radius_km = models.FloatField(
        default=20.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(200.0)],
        help_text="Service radius in kilometers"
    )
    
    # Verification
    is_identity_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending'
    )
    verification_document = models.FileField(upload_to='verification_docs/', null=True, blank=True)
    verification_date = models.DateTimeField(null=True, blank=True)
    verification_expires_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True, null=True)
    
    # Professional details
    years_in_business = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    company_size = models.CharField(max_length=50, blank=True, null=True)
    insurance_verified = models.BooleanField(default=False)
    insurance_document = models.FileField(upload_to='insurance_docs/', null=True, blank=True)
    
    # Website and social
    website = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    
    # Availability
    is_accepting_jobs = models.BooleanField(default=True)
    average_response_time_hours = models.FloatField(default=24.0)
    
    # Analytics
    total_jobs_completed = models.IntegerField(default=0)
    profile_views = models.IntegerField(default=0)
    contact_clicks = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contractor_profiles'
        indexes = [
            models.Index(fields=['verification_status']),
            models.Index(fields=['is_identity_verified']),
            models.Index(fields=['is_accepting_jobs']),
        ]
    
    def __str__(self):
        return f"{self.business_name or self.user.get_full_name()} - Contractor"
    
    def set_office_location(self, latitude, longitude):
        """Set office location using lat/lng coordinates"""
        self.office_location = Point(longitude, latitude, srid=4326)
        self.save()
    
    def get_overall_trust_score(self):
        """Calculate average trust score across all services"""
        from apps.services.models import ContractorService
        services = ContractorService.objects.filter(contractor=self)
        if not services.exists():
            return 0.0
        avg_score = services.aggregate(models.Avg('trust_score'))['trust_score__avg']
        return round(avg_score or 0.0, 2)


class ContractorDispute(models.Model):
    """Handle disputes raised by contractors"""
    
    DISPUTE_STATUS = (
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    )
    
    DISPUTE_TYPE = (
        ('unfair_trust', 'Unfair Trust Mark'),
        ('fraudulent_review', 'Fraudulent Review'),
        ('identity_theft', 'Identity Theft'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contractor = models.ForeignKey(
        ContractorProfile,
        on_delete=models.CASCADE,
        related_name='disputes'
    )
    dispute_type = models.CharField(max_length=50, choices=DISPUTE_TYPE)
    status = models.CharField(max_length=20, choices=DISPUTE_STATUS, default='open')
    
    # Reference to what's being disputed
    trust_mark = models.ForeignKey(
        'trust.TrustMark',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='disputes'
    )
    
    # Dispute details
    description = models.TextField()
    evidence = models.FileField(upload_to='dispute_evidence/', null=True, blank=True)
    
    # Resolution
    admin_notes = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_disputes'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contractor_disputes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contractor', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['dispute_type']),
        ]
    
    def __str__(self):
        return f"Dispute #{self.id} - {self.contractor.business_name} - {self.status}"


class ContractorAnalytics(models.Model):
    """Track contractor performance metrics over time"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contractor = models.ForeignKey(
        ContractorProfile,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    date = models.DateField()
    
    # Metrics
    profile_views = models.IntegerField(default=0)
    search_appearances = models.IntegerField(default=0)
    contact_clicks = models.IntegerField(default=0)
    trust_marks_received = models.IntegerField(default=0)
    average_trust_score = models.FloatField(default=0.0)
    
    # Rankings
    local_rank = models.IntegerField(null=True, blank=True)
    category_rank = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'contractor_analytics'
        unique_together = ['contractor', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['contractor', '-date']),
        ]
    
    def __str__(self):
        return f"{self.contractor.business_name} - {self.date}"
