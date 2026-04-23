from django.core.management.base import BaseCommand
from apps.trust.utils import batch_update_all_trust_scores
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Recomputes trust scores for all active contractor services.'

    def handle(self, *args, **options):
        self.stdout.write("Starting batch trust score recomputation...")
        logger.info("Starting batch trust score recomputation via management command")
        
        result = batch_update_all_trust_scores()
        
        summary = (
            f"Batch recomputation complete: {result['updated']} updated, "
            f"{result['errors']} errors out of {result['total']} total active services."
        )
        self.stdout.write(self.style.SUCCESS(summary))
        logger.info(summary)
