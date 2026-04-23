from django.db import migrations


class Migration(migrations.Migration):
    """
    Rename total_trust_marks → total_feedbacks and
    verified_trust_marks → verified_feedbacks on ContractorService.

    After migration 0003_feedback_model in the trust app, these fields
    count Feedback rows, not TrustMark rows. The misleading names were
    inherited from before the refactor.
    """

    dependencies = [
        ('services', '0002_servicesubcategory_contractorservice_subcategories_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contractorservice',
            old_name='total_trust_marks',
            new_name='total_feedbacks',
        ),
        migrations.RenameField(
            model_name='contractorservice',
            old_name='verified_trust_marks',
            new_name='verified_feedbacks',
        ),
    ]
