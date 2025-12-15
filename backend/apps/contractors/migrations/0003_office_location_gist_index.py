from django.db import migrations
from django.contrib.postgres.indexes import GistIndex


class Migration(migrations.Migration):
    dependencies = [
        ('contractors', '0002_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='contractorprofile',
            index=GistIndex(fields=['office_location'], name='contractor_office_location_gist'),
        ),
    ]
