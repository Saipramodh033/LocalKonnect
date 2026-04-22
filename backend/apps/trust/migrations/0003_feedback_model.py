from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


def migrate_feedback_from_trust_and_review(apps, schema_editor):
    TrustMark = apps.get_model('trust', 'TrustMark')
    Feedback = apps.get_model('trust', 'Feedback')

    for trust_mark in TrustMark.objects.all().order_by('created_at'):
        rating = 5
        text = trust_mark.review_text

        try:
            review = trust_mark.detailed_review
        except Exception:
            review = None

        if review is not None:
            if review.rating:
                rating = review.rating
            if review.text:
                text = review.text

        feedback, _ = Feedback.objects.update_or_create(
            customer_id=trust_mark.customer_id,
            contractor_service_id=trust_mark.contractor_service_id,
            defaults={
                'rating': rating,
                'text': text,
                'is_verified': trust_mark.is_verified,
                'ip_address': trust_mark.ip_address,
                'user_agent': trust_mark.user_agent,
            },
        )

        # Keep original trust mark timestamps for continuity.
        Feedback.objects.filter(pk=feedback.pk).update(
            created_at=trust_mark.created_at,
            updated_at=trust_mark.updated_at,
        )

        if trust_mark.verification_proof:
            feedback.verification_proof = trust_mark.verification_proof
            feedback.save(update_fields=['verification_proof'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('services', '0002_servicesubcategory_contractorservice_subcategories_and_more'),
        ('trust', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('rating', models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])),
                ('text', models.TextField(blank=True, max_length=1000, null=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('verification_proof', models.FileField(blank=True, help_text='Optional proof of verified job completion', null=True, upload_to='feedback_verification/')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contractor_service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback_entries', to='services.contractorservice')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'feedback',
                'ordering': ['-updated_at'],
                'unique_together': {('customer', 'contractor_service')},
            },
        ),
        migrations.AddIndex(
            model_name='feedback',
            index=models.Index(fields=['contractor_service', '-updated_at'], name='feedback_contrac_36fd47_idx'),
        ),
        migrations.AddIndex(
            model_name='feedback',
            index=models.Index(fields=['customer', '-created_at'], name='feedback_custome_88c0ba_idx'),
        ),
        migrations.AddIndex(
            model_name='feedback',
            index=models.Index(fields=['rating'], name='feedback_rating_d746a3_idx'),
        ),
        migrations.AddIndex(
            model_name='feedback',
            index=models.Index(fields=['is_verified'], name='feedback_is_ver_2b64de_idx'),
        ),
        migrations.RunPython(migrate_feedback_from_trust_and_review, noop_reverse),
    ]
