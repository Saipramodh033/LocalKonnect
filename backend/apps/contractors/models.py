from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.contrib.postgres.indexes import GistIndex
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
            GistIndex(fields=['office_location'], name='contractor_office_location_gist'),
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

