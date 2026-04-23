from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
import uuid


class User(AbstractUser):
    """Custom user model supporting both Contractors and Customers"""
    
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('contractor', 'Contractor'),
        ('admin', 'Admin'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    
    # Location (for customers - home location)
    location = gis_models.PointField(geography=True, null=True, blank=True, srid=4326)
    address = models.CharField(max_length=500, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Profile
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    
    # Trust metrics (for customers giving reviews)
    reviewer_weight = models.FloatField(default=0.6)  # Increases with verified status
    is_verified_reviewer = models.BooleanField(default=False)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Flags and moderation
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.TextField(blank=True, null=True)
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'user_type']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['is_email_verified']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.user_type})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def set_location(self, latitude, longitude):
        """Set user location using lat/lng coordinates"""
        self.location = Point(longitude, latitude, srid=4326)
        self.save()



