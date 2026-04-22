from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contractors', '0004_dispute_feedback_fk'),
        ('trust', '0003_feedback_model'),
    ]

    operations = [
        migrations.DeleteModel(
            name='FraudPattern',
        ),
        migrations.DeleteModel(
            name='Review',
        ),
        migrations.DeleteModel(
            name='TrustMark',
        ),
    ]
