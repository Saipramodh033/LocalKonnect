from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contractors', '0003_office_location_gist_index'),
        ('trust', '0003_feedback_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contractordispute',
            name='trust_mark',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='disputes', to='trust.feedback'),
        ),
    ]
