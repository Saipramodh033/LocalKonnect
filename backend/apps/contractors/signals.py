from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.gis.geos import Point
import logging

from apps.users.models import User
from .models import ContractorProfile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_contractor_profile(sender, instance: User, created: bool, **kwargs):
    """Auto-create a ContractorProfile for users marked as contractors."""
    if not created:
        return
    
    if instance.user_type == 'contractor':
        try:
            ContractorProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'office_address': 'Not set',
                    'office_location': Point(0, 0, srid=4326),
                    # Prevent appearing in search until the contractor sets a
                    # real office location and explicitly opens for business.
                    'is_accepting_jobs': False,
                }
            )
            logger.info(f"ContractorProfile created for user {instance.email}")
        except Exception as e:
            logger.error(f"Failed to create ContractorProfile for {instance.email}: {e}")
            # Re-raise during non-migration scenarios
            if 'migrate' not in ' '.join(__import__('sys').argv):
                raise