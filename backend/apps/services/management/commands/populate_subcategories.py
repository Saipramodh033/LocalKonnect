"""
Management command to populate service subcategories
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.services.models import ServiceCategory, ServiceSubcategory


class Command(BaseCommand):
    help = 'Populate service subcategories for each category'

    def handle(self, *args, **options):
        self.stdout.write('Creating service subcategories...')
        
        # Define subcategories for each service category
        subcategories_data = {
            'Plumbing': [
                'Pipe Repair', 'Drain Cleaning', 'Water Heater Installation',
                'Bathroom Plumbing', 'Kitchen Plumbing', 'Emergency Plumbing',
                'Leak Detection', 'Toilet Repair', 'Faucet Installation',
                'Sewer Line Repair', 'Gas Line Installation'
            ],
            'Electrical': [
                'Wiring Installation', 'Panel Upgrades', 'Lighting Installation',
                'Ceiling Fan Installation', 'Outlet Repair', 'Circuit Breaker Repair',
                'Electrical Inspection', 'Generator Installation', 'Smart Home Wiring',
                'Security System Wiring', 'EV Charger Installation'
            ],
            'HVAC': [
                'AC Installation', 'AC Repair', 'Heating Installation',
                'Heating Repair', 'Duct Cleaning', 'Duct Installation',
                'Thermostat Installation', 'Air Quality Testing', 'Ventilation Repair',
                'Heat Pump Installation', 'Furnace Repair'
            ],
            'Carpentry': [
                'Custom Cabinets', 'Deck Building', 'Furniture Repair',
                'Door Installation', 'Window Installation', 'Crown Molding',
                'Trim Work', 'Shelving Installation', 'Framing',
                'Custom Woodwork', 'Staircase Repair'
            ],
            'Painting': [
                'Interior Painting', 'Exterior Painting', 'Wall Painting',
                'Ceiling Painting', 'Floor Painting', 'Cabinet Refinishing',
                'Deck Staining', 'Fence Painting', 'Pressure Washing',
                'Wallpaper Removal', 'Drywall Repair'
            ],
            'Landscaping': [
                'Lawn Care', 'Lawn Mowing', 'Garden Design',
                'Tree Services', 'Tree Trimming', 'Irrigation Installation',
                'Sod Installation', 'Mulching', 'Hedge Trimming',
                'Landscape Lighting', 'Hardscaping', 'Patio Installation'
            ],
            'Roofing': [
                'Roof Replacement', 'Roof Repair', 'Leak Repair',
                'Gutter Installation', 'Gutter Cleaning', 'Shingle Replacement',
                'Flat Roof Repair', 'Skylight Installation', 'Chimney Repair',
                'Roof Inspection', 'Storm Damage Repair'
            ],
            'Cleaning': [
                'House Cleaning', 'Deep Cleaning', 'Move-out Cleaning',
                'Move-in Cleaning', 'Carpet Cleaning', 'Window Cleaning',
                'Office Cleaning', 'Post-Construction Cleaning', 'Upholstery Cleaning',
                'Tile and Grout Cleaning', 'Pressure Washing'
            ],
        }
        
        total_created = 0
        
        for category_name, subcategory_names in subcategories_data.items():
            try:
                category = ServiceCategory.objects.get(name=category_name)
                
                for idx, subcat_name in enumerate(subcategory_names):
                    subcategory, created = ServiceSubcategory.objects.get_or_create(
                        category=category,
                        slug=slugify(subcat_name),
                        defaults={
                            'name': subcat_name,
                            'is_active': True,
                            'display_order': idx,
                        }
                    )
                    
                    if created:
                        total_created += 1
                        self.stdout.write(f'  Created: {category_name} -> {subcat_name}')
                        
            except ServiceCategory.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Category "{category_name}" not found, skipping...'))
                continue
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {total_created} subcategories!'))
