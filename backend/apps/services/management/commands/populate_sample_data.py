"""
Management command to populate sample data for testing
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.contrib.gis.geos import Point
from apps.users.models import User
from apps.contractors.models import ContractorProfile
from apps.services.models import ServiceCategory, ContractorService
import random


class Command(BaseCommand):
    help = 'Populate database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create service categories
        categories_data = [
            {'name': 'Plumbing', 'icon': '🔧'},
            {'name': 'Electrical', 'icon': '⚡'},
            {'name': 'HVAC', 'icon': '❄️'},
            {'name': 'Carpentry', 'icon': '🔨'},
            {'name': 'Painting', 'icon': '🎨'},
            {'name': 'Landscaping', 'icon': '🌳'},
            {'name': 'Roofing', 'icon': '🏠'},
            {'name': 'Cleaning', 'icon': '🧹'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                slug=slugify(cat_data['name']),
                defaults={
                    'name': cat_data['name'],
                    'icon': cat_data['icon'],
                    'is_active': True,
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create sample contractors
        contractors_data = [
            {
                'email': 'john.plumber@example.com',
                'first_name': 'John',
                'last_name': 'Smith',
                'business_name': 'Smith Plumbing Services',
                'address': '123 Main St, New York, NY 10001',
                'lat': 40.7589,
                'lng': -73.9851,
                'years': 15,
            },
            {
                'email': 'mike.electric@example.com',
                'first_name': 'Mike',
                'last_name': 'Johnson',
                'business_name': 'Johnson Electric Co.',
                'address': '456 Broadway, New York, NY 10012',
                'lat': 40.7214,
                'lng': -74.0022,
                'years': 10,
            },
            {
                'email': 'sarah.hvac@example.com',
                'first_name': 'Sarah',
                'last_name': 'Williams',
                'business_name': 'Williams HVAC Solutions',
                'address': '789 5th Ave, New York, NY 10021',
                'lat': 40.7736,
                'lng': -73.9656,
                'years': 8,
            },
            {
                'email': 'tom.carpenter@example.com',
                'first_name': 'Tom',
                'last_name': 'Brown',
                'business_name': 'Brown Carpentry',
                'address': '321 Park Ave, New York, NY 10022',
                'lat': 40.7614,
                'lng': -73.9776,
                'years': 12,
            },
            {
                'email': 'lisa.painter@example.com',
                'first_name': 'Lisa',
                'last_name': 'Davis',
                'business_name': 'Davis Painting & Decor',
                'address': '654 Madison Ave, New York, NY 10065',
                'lat': 40.7654,
                'lng': -73.9682,
                'years': 7,
            },
        ]
        
        for contractor_data in contractors_data:
            # Create or get user
            user, created = User.objects.get_or_create(
                email=contractor_data['email'],
                defaults={
                    'username': contractor_data['email'],
                    'first_name': contractor_data['first_name'],
                    'last_name': contractor_data['last_name'],
                    'user_type': 'contractor',
                }
            )
            
            if created:
                user.set_password('contractor123')
                user.save()
                self.stdout.write(f'Created contractor user: {user.email}')
            
            # Create contractor profile
            profile, created = ContractorProfile.objects.get_or_create(
                user=user,
                defaults={
                    'business_name': contractor_data['business_name'],
                    'office_address': contractor_data['address'],
                    'office_location': Point(contractor_data['lng'], contractor_data['lat']),
                    'service_radius_km': random.choice([10, 15, 20, 25, 30]),
                    'years_in_business': contractor_data['years'],
                    'is_identity_verified': random.choice([True, True, False]),
                    'verification_status': random.choice(['verified', 'verified', 'pending']),
                    'is_accepting_jobs': True,
                    'total_jobs_completed': random.randint(10, 100),
                    'profile_views': random.randint(50, 500),
                    'company_size': random.choice(['1-5 employees', '6-10 employees', '11-20 employees']),
                }
            )
            
            if created:
                self.stdout.write(f'Created contractor profile: {profile.business_name}')
            
            # Create services for this contractor
            num_services = random.randint(1, 3)
            for i in range(num_services):
                category = random.choice(categories)
                
                service_titles = {
                    'Plumbing': ['Emergency Plumbing', 'Bathroom Renovation', 'Pipe Repair'],
                    'Electrical': ['Wiring Installation', 'Panel Upgrades', 'Lighting Installation'],
                    'HVAC': ['AC Installation', 'Heating Repair', 'Duct Cleaning'],
                    'Carpentry': ['Custom Cabinets', 'Deck Building', 'Furniture Repair'],
                    'Painting': ['Interior Painting', 'Exterior Painting', 'Cabinet Refinishing'],
                    'Landscaping': ['Lawn Care', 'Garden Design', 'Tree Services'],
                    'Roofing': ['Roof Replacement', 'Leak Repair', 'Gutter Installation'],
                    'Cleaning': ['House Cleaning', 'Deep Cleaning', 'Move-out Cleaning'],
                }
                
                title = random.choice(service_titles.get(category.name, ['General Services']))
                
                service, created = ContractorService.objects.get_or_create(
                    contractor=profile,
                    category=category,
                    title=title,
                    defaults={
                        'description': f'Professional {title.lower()} services with years of experience. Quality work guaranteed.',
                        'years_of_experience': random.randint(3, contractor_data['years']),
                        'min_price': random.randint(50, 200),
                        'max_price': random.randint(300, 1000),
                        'pricing_model': random.choice(['hourly', 'fixed', 'quote']),
                        'trust_score': random.uniform(20, 95),
                        'total_trust_marks': random.randint(5, 50),
                        'verified_trust_marks': random.randint(2, 30),
                    }
                )
                
                if created:
                    self.stdout.write(f'  - Created service: {service.title}')
        
        self.stdout.write(self.style.SUCCESS('Sample data creation completed!'))
        self.stdout.write(f'Created {len(categories)} categories')
        self.stdout.write(f'Created {len(contractors_data)} contractors')
        self.stdout.write(f'Created {ContractorService.objects.count()} services')
