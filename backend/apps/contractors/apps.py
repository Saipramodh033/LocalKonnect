from django.apps import AppConfig


class ContractorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.contractors'
    verbose_name = 'Contractors'

    def ready(self):
        # Import signals to ensure handlers are registered
        from . import signals  # noqa: F401
