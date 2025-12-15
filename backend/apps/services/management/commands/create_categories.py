"""
Management command to create initial service categories
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.services.models import ServiceCategory


class Command(BaseCommand):
    help = 'Create initial service categories'

    def handle(self, *args, **options):
        categories = [
            {'name': 'Plumbing', 'icon': '🔧', 'description': 'Plumbing installation, repair, and maintenance'},
            {'name': 'Electrical', 'icon': '⚡', 'description': 'Electrical wiring, repairs, and installations'},
            {'name': 'HVAC', 'icon': '🌡️', 'description': 'Heating, ventilation, and air conditioning services'},
            {'name': 'Carpentry', 'icon': '🔨', 'description': 'Custom woodwork and carpentry services'},
            {'name': 'Painting', 'icon': '🎨', 'description': 'Interior and exterior painting services'},
            {'name': 'Landscaping', 'icon': '🌳', 'description': 'Lawn care and landscape design'},
            {'name': 'Roofing', 'icon': '🏠', 'description': 'Roof installation, repair, and maintenance'},
            {'name': 'Cleaning', 'icon': '🧹', 'description': 'Residential and commercial cleaning services'},
            {'name': 'Renovation', 'icon': '🏗️', 'description': 'Home renovation and remodeling'},
            {'name': 'Flooring', 'icon': '📐', 'description': 'Flooring installation and repair'},
        ]

        created = 0
        for idx, cat in enumerate(categories, 1):
            obj, was_created = ServiceCategory.objects.get_or_create(
                slug=slugify(cat['name']),
                defaults={
                    'name': cat['name'],
                    'icon': cat.get('icon', ''),
                    'description': cat.get('description', ''),
                    'is_active': True,
                    'display_order': idx * 10,
                }
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {cat["name"]}'))
            else:
                self.stdout.write(f'Category already exists: {cat["name"]}')

        self.stdout.write(self.style.SUCCESS(f'\nTotal categories created: {created}'))
        self.stdout.write(f'Total categories in database: {ServiceCategory.objects.count()}')
