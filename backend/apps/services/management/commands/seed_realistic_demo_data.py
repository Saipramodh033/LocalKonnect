"""
Management command to seed realistic demo data that follows LocalKonnect flows.

Creates:
- 10 contractor users + profiles
- 10 customer users
- Service categories and subcategories
- Contractor services tied to categories/subcategories
- Feedback from customers to services
- Trust score history via trust score recalculation

The command is rerunnable. It removes prior seed users by domain before recreating data.
"""

from datetime import timedelta
import random

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.contractors.models import ContractorProfile
from apps.services.models import ContractorService, ServiceCategory, ServiceSubcategory
from apps.trust.models import Feedback
from apps.trust.utils import update_service_trust_score
from apps.users.models import User


class Command(BaseCommand):
    help = "Seed realistic demo data: 10 contractors, 10 customers, and related entities"

    seed_domain = "seed.localkonnect.test"

    def handle(self, *args, **options):
        random.seed(20260421)
        now = timezone.now()

        self.stdout.write("Removing previous seed data (if any)...")
        removed_count = User.objects.filter(email__endswith=f"@{self.seed_domain}").count()
        User.objects.filter(email__endswith=f"@{self.seed_domain}").delete()
        self.stdout.write(f"Removed seed users: {removed_count}")

        categories = self._ensure_categories_and_subcategories()
        contractors = self._create_contractors(now)
        customers = self._create_customers(now)
        services = self._create_services(contractors, categories, now)

        feedback_count = self._create_feedback(customers, services, now)
        self._recalculate_scores(services)

        self.stdout.write(self.style.SUCCESS("Seed completed successfully."))
        self.stdout.write(f"Contractors created: {len(contractors)}")
        self.stdout.write(f"Customers created: {len(customers)}")
        self.stdout.write(f"Services created: {len(services)}")
        self.stdout.write(f"Feedback created: {feedback_count}")

    def _ensure_categories_and_subcategories(self):
        categories_data = [
            "Plumbing",
            "Electrical",
            "HVAC",
            "Carpentry",
            "Painting",
            "Landscaping",
            "Roofing",
            "Cleaning",
            "Renovation",
            "Flooring",
        ]

        category_to_subcategories = {
            "Plumbing": ["Pipe Repair", "Drain Cleaning", "Leak Detection"],
            "Electrical": ["Wiring Installation", "Panel Upgrades", "Lighting Installation"],
            "HVAC": ["AC Repair", "Heating Repair", "Duct Cleaning"],
            "Carpentry": ["Custom Cabinets", "Deck Building", "Trim Work"],
            "Painting": ["Interior Painting", "Exterior Painting", "Wall Prep"],
            "Landscaping": ["Lawn Care", "Garden Design", "Tree Trimming"],
            "Roofing": ["Roof Repair", "Shingle Replacement", "Gutter Installation"],
            "Cleaning": ["Deep Cleaning", "Move-out Cleaning", "Window Cleaning"],
            "Renovation": ["Kitchen Remodel", "Bathroom Remodel", "Basement Finishing"],
            "Flooring": ["Tile Installation", "Hardwood Installation", "Laminate Repair"],
        }

        categories = []
        for idx, name in enumerate(categories_data, start=1):
            category, _ = ServiceCategory.objects.get_or_create(
                slug=slugify(name),
                defaults={
                    "name": name,
                    "is_active": True,
                    "display_order": idx * 10,
                },
            )
            categories.append(category)

            for sub_idx, sub_name in enumerate(category_to_subcategories[name], start=1):
                ServiceSubcategory.objects.get_or_create(
                    category=category,
                    slug=slugify(sub_name),
                    defaults={
                        "name": sub_name,
                        "is_active": True,
                        "display_order": sub_idx,
                    },
                )

        return categories

    def _create_contractors(self, now):
        first_names = ["Aarav", "Mason", "Sophia", "Liam", "Noah", "Olivia", "Ethan", "Ava", "Lucas", "Mia"]
        last_names = ["Patel", "Turner", "Reed", "Bennett", "Foster", "Rivera", "Cooper", "Hughes", "Ward", "Brooks"]
        businesses = [
            "NorthStar Home Services",
            "BlueLine Electrical",
            "CityCore HVAC",
            "CraftNest Carpentry",
            "PrimeCoat Painting",
            "GreenSpan Landscaping",
            "SummitPeak Roofing",
            "SparklePro Cleaning",
            "UrbanEdge Renovation",
            "SolidStep Flooring",
        ]
        addresses = [
            "120 Main St, New York, NY 10001",
            "415 Broadway, New York, NY 10012",
            "89 Lexington Ave, New York, NY 10016",
            "230 Park Ave, New York, NY 10017",
            "17 8th Ave, New York, NY 10014",
            "61 Columbus Ave, New York, NY 10023",
            "742 Amsterdam Ave, New York, NY 10025",
            "305 E 86th St, New York, NY 10028",
            "520 Atlantic Ave, Brooklyn, NY 11217",
            "96 Court St, Brooklyn, NY 11201",
        ]
        coords = [
            (40.7505, -73.9934),
            (40.7196, -74.0018),
            (40.7421, -73.9826),
            (40.7544, -73.9779),
            (40.7383, -74.0020),
            (40.7808, -73.9730),
            (40.7905, -73.9723),
            (40.7789, -73.9545),
            (40.6867, -73.9773),
            (40.6912, -73.9918),
        ]

        contractors = []
        for i in range(10):
            email = f"contractor{i + 1}@{self.seed_domain}"
            username = f"seed_contractor_{i + 1}"
            user = User.objects.create_user(
                email=email,
                username=username,
                password="SeedPass123!",
                user_type="contractor",
                first_name=first_names[i],
                last_name=last_names[i],
                is_email_verified=True,
                phone_number=f"+1-555-410-{1000 + i}",
                created_at=now - timedelta(days=90 + i),
            )

            profile, _ = ContractorProfile.objects.get_or_create(
                user=user,
                defaults={
                    "office_address": addresses[i],
                    "office_location": Point(coords[i][1], coords[i][0], srid=4326),
                },
            )
            profile.business_name = businesses[i]
            profile.office_address = addresses[i]
            profile.office_location = Point(coords[i][1], coords[i][0], srid=4326)
            profile.service_radius_km = random.choice([10, 15, 20, 25, 30])
            profile.years_in_business = random.randint(4, 18)
            profile.company_size = random.choice(["1-5 employees", "6-10 employees", "11-20 employees"])
            profile.is_identity_verified = i % 4 != 0
            profile.verification_status = "verified" if profile.is_identity_verified else "pending"
            profile.is_accepting_jobs = True
            profile.total_jobs_completed = random.randint(20, 220)
            profile.profile_views = random.randint(80, 1200)
            profile.contact_clicks = random.randint(10, 300)
            profile.average_response_time_hours = random.choice([1.5, 2.0, 3.0, 6.0, 12.0])
            profile.save()

            contractors.append(profile)

        return contractors

    def _create_customers(self, now):
        first_names = ["Emma", "James", "Amelia", "Benjamin", "Charlotte", "Elijah", "Harper", "Henry", "Evelyn", "Alexander"]
        last_names = ["Miller", "Davis", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris"]
        coords = [
            (40.7484, -73.9857),
            (40.7306, -73.9866),
            (40.7616, -73.9817),
            (40.7060, -74.0086),
            (40.7128, -74.0060),
            (40.7527, -73.9772),
            (40.7359, -73.9911),
            (40.7580, -73.9855),
            (40.7411, -73.9897),
            (40.7218, -73.9996),
        ]

        customers = []
        for i in range(10):
            email = f"customer{i + 1}@{self.seed_domain}"
            username = f"seed_customer_{i + 1}"
            is_verified_reviewer = i % 3 != 0

            user = User.objects.create_user(
                email=email,
                username=username,
                password="SeedPass123!",
                user_type="customer",
                first_name=first_names[i],
                last_name=last_names[i],
                is_email_verified=True,
                phone_number=f"+1-555-510-{1000 + i}",
                is_verified_reviewer=is_verified_reviewer,
                reviewer_weight=1.0 if is_verified_reviewer else 0.6,
                address=f"Apartment {10 + i}, Seed Residency",
                city="New York",
                state="NY",
                country="USA",
                postal_code=f"100{10 + i}",
                created_at=now - timedelta(days=45 + i),
            )
            user.location = Point(coords[i][1], coords[i][0], srid=4326)
            user.save(update_fields=["location"])

            customers.append(user)

        return customers

    def _create_services(self, contractors, categories, now):
        services = []

        for idx, contractor in enumerate(contractors):
            selected_categories = random.sample(categories, k=2)
            for cat_idx, category in enumerate(selected_categories):
                title = f"{category.name} Services - {contractor.business_name}"
                years_exp = max(1, contractor.years_in_business - random.randint(0, 3))
                min_price = random.randint(60, 250)
                max_price = min_price + random.randint(150, 900)

                service = ContractorService.objects.create(
                    contractor=contractor,
                    category=category,
                    title=title,
                    description=(
                        f"Professional {category.name.lower()} solutions by {contractor.business_name}. "
                        "Focused on timely delivery, transparent pricing, and clean workmanship."
                    ),
                    years_of_experience=years_exp,
                    min_price=min_price,
                    max_price=max_price,
                    pricing_model=random.choice(["hourly", "fixed", "quote"]),
                    is_active=True,
                    is_featured=(idx + cat_idx) % 5 == 0,
                    total_jobs=random.randint(8, 140),
                    views_count=random.randint(30, 900),
                    created_at=now - timedelta(days=random.randint(10, 120)),
                )

                subs = list(ServiceSubcategory.objects.filter(category=category, is_active=True)[:3])
                if subs:
                    service.subcategories.set(random.sample(subs, k=min(2, len(subs))))

                services.append(service)

        return services

    def _create_feedback(self, customers, services, now):
        feedback_created = 0

        for customer_idx, customer in enumerate(customers):
            picked_services = random.sample(services, k=3)

            for service_idx, service in enumerate(picked_services):
                verified = (customer_idx + service_idx) % 2 == 0
                Feedback.objects.create(
                    customer=customer,
                    contractor_service=service,
                    rating=random.randint(3, 5),
                    text=(
                        f"Completed a {service.category.name.lower()} job with good communication and clean handover. "
                        f"Customer seed note #{customer_idx + 1}-{service_idx + 1}."
                    ),
                    is_verified=verified,
                    ip_address=f"10.10.{customer_idx}.{service_idx + 10}",
                    user_agent="SeedDataScript/1.0",
                    created_at=now - timedelta(days=random.randint(1, 30)),
                )
                feedback_created += 1

        return feedback_created

    def _recalculate_scores(self, services):
        for service in services:
            update_service_trust_score(service)
