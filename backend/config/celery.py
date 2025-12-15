from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('localkonnect')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


# Periodic tasks
app.conf.beat_schedule = {
    'recompute-trust-scores-nightly': {
        'task': 'apps.trust.tasks.batch_recompute_trust_scores',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
    'scan-fraud-patterns': {
        'task': 'apps.trust.tasks.scan_fraud_patterns',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'cleanup-expired-verifications': {
        'task': 'apps.contractors.tasks.cleanup_expired_verifications',
        'schedule': crontab(hour=3, minute=0),  # Run at 3 AM daily
    },
    'refresh-ranking-cache': {
        'task': 'apps.search.tasks.refresh_ranking_cache',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
