"""
User signals for post-save actions
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from apps.contractors.models import ContractorProfile


@receiver(post_save, sender=User)
def create_contractor_profile(sender, instance, created, **kwargs):
    """Create contractor profile when contractor user is created"""
    if created and instance.user_type == 'contractor':
        # Create basic contractor profile
        # Location will be set later by the contractor
        pass  # Will be created via API when contractor sets up profile
