from django.db import migrations


class Migration(migrations.Migration):
    """
    Remove ContractorDispute and ContractorAnalytics.

    Neither model is referenced by any view, signal, task, or template.
    ContractorDispute was updated to FK→Feedback during refactoring but
    has no UI or API surface. ContractorAnalytics has never been written to.
    """

    dependencies = [
        ('contractors', '0004_dispute_feedback_fk'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ContractorAnalytics',
        ),
        migrations.DeleteModel(
            name='ContractorDispute',
        ),
    ]
