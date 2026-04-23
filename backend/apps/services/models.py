from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.contractors.models import ContractorProfile
import uuid


class ServiceCategory(models.Model):
    """Categories for contractor services"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # Icon class or emoji
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_categories'
        verbose_name_plural = 'Service Categories'
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class ServiceSubcategory(models.Model):
    """Predefined subcategories for services (e.g., Wall Painting, Floor Painting)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='predefined_subcategories'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_subcategories'
        verbose_name_plural = 'Service Subcategories'
        unique_together = ['category', 'slug']
        ordering = ['category', 'display_order', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class ContractorService(models.Model):
    """Services offered by contractors with per-service trust scores"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contractor = models.ForeignKey(
        ContractorProfile,
        on_delete=models.CASCADE,
        related_name='services'
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name='contractor_services'
    )
    
    # Selected subcategories (many-to-many relationship)
    subcategories = models.ManyToManyField(
        ServiceSubcategory,
        related_name='contractor_services',
        blank=True,
        help_text="Specific subcategories this contractor offers"
    )
    
    # Service details
    title = models.CharField(max_length=255)
    description = models.TextField()
    years_of_experience = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Pricing (optional)
    min_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum price for this service"
    )
    max_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum price for this service"
    )
    pricing_model = models.CharField(
        max_length=50,
        choices=[
            ('hourly', 'Hourly Rate'),
            ('fixed', 'Fixed Price'),
            ('quote', 'By Quote'),
        ],
        default='quote'
    )
    
    # Trust metrics (calculated by trust engine)
    trust_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Calculated trust score (0-100)"
    )
    total_trust_marks = models.IntegerField(default=0)
    verified_trust_marks = models.IntegerField(default=0)
    trust_score_last_calculated = models.DateTimeField(null=True, blank=True)
    
    # Portfolio
    portfolio_images = models.JSONField(
        default=list,
        blank=True,
        help_text="List of portfolio image URLs"
    )
    certifications = models.JSONField(
        default=list,
        blank=True,
        help_text="List of certifications for this service"
    )
    
    # Availability
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Statistics
    total_jobs = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contractor_services'
        unique_together = ['contractor', 'category']
        ordering = ['-trust_score', '-created_at']
        indexes = [
            models.Index(fields=['contractor', 'category']),
            models.Index(fields=['category', '-trust_score']),
            models.Index(fields=['is_active', '-trust_score']),
        ]
    
    def __str__(self):
        return f"{self.contractor.business_name} - {self.category.name}"
    
    def get_trust_score_color(self):
        """Return color code based on trust score"""
        if self.trust_score >= 60:
            return 'green'
        elif self.trust_score >= 20:
            return 'yellow'
        else:
            return 'red'
    
    def trigger_trust_recalculation(self):
        """Recalculate and persist trust score synchronously.

        The score is always updated in the same DB transaction as the feedback
        save so it is immediately consistent.  A Celery task is dispatched
        afterwards as a best-effort audit log writer — if the broker is
        unavailable the score is still correct.
        """
        from apps.trust.utils import update_service_trust_score
        import logging
        _log = logging.getLogger(__name__)

        # Always run synchronously first — score must never depend on Celery.
        try:
            update_service_trust_score(self)
        except Exception as exc:
            _log.error(
                "Synchronous trust score update failed for service %s: %s",
                self.id, exc, exc_info=True,
            )
            raise  # Re-raise so the caller (Feedback.save) knows it failed.

        # Best-effort async dispatch for any additional worker-side processing.
        try:
            from apps.trust.tasks import recalculate_service_trust_score
            recalculate_service_trust_score.delay(str(self.id))
        except Exception as exc:
            _log.warning(
                "Celery dispatch skipped for service %s (broker unavailable?): %s",
                self.id, exc,
            )


class ServicePortfolioItem(models.Model):
    """Portfolio items for contractor services"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(
        ContractorService,
        on_delete=models.CASCADE,
        related_name='portfolio_items'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='portfolio/')
    completion_date = models.DateField(null=True, blank=True)
    project_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    client_name = models.CharField(max_length=255, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_portfolio_items'
        ordering = ['display_order', '-created_at']
        indexes = [
            models.Index(fields=['service', 'is_featured']),
        ]
    
    def __str__(self):
        return f"{self.service.contractor.business_name} - {self.title}"
