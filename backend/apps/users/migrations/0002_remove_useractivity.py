from django.db import migrations


class Migration(migrations.Migration):
    """
    Remove UserActivity model.

    UserActivity was defined but never written to from any view, signal,
    or task in the codebase. It tracked login/trust-mark/review events
    referencing the now-deleted TrustMark/Review models.
    """

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UserActivity',
        ),
    ]
