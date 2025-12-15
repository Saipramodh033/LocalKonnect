"""
Forms for contractor profile and service management
"""

from django import forms
from apps.contractors.models import ContractorProfile
from apps.services.models import ContractorService, ServiceCategory, ServiceSubcategory


class ContractorProfileForm(forms.ModelForm):
    """Form for editing contractor profile"""
    
    class Meta:
        model = ContractorProfile
        fields = [
            'business_name', 'business_registration_number', 'office_address',
            'service_radius_km', 'years_in_business', 'company_size',
            'website', 'linkedin', 'facebook', 'is_accepting_jobs'
        ]
        widgets = {
            'business_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'business_registration_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'office_address': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'service_radius_km': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.1'
            }),
            'years_in_business': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'company_size': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'is_accepting_jobs': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
        }


class ContractorServiceForm(forms.ModelForm):
    """Form for adding/editing contractor services with dynamic subcategories"""
    
    subcategories = forms.ModelMultipleChoiceField(
        queryset=ServiceSubcategory.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'subcategory-select',
            'style': 'display: none;'  # Hidden, we'll use custom UI
        })
    )
    
    class Meta:
        model = ContractorService
        fields = [
            'category', 'title', 'description', 'years_of_experience',
            'min_price', 'max_price', 'pricing_model', 'subcategories'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'id': 'id_category',
                'onchange': 'loadSubcategories(this.value)'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4
            }),
            'years_of_experience': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'min_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.01'
            }),
            'max_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.01'
            }),
            'pricing_model': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing existing service, load subcategories for that category
        if self.instance and self.instance.pk and hasattr(self.instance, 'category') and self.instance.category:
            self.fields['subcategories'].queryset = ServiceSubcategory.objects.filter(
                category=self.instance.category,
                is_active=True
            )
        elif self.data and 'category' in self.data:
            # For form submission (POST data), load subcategories for selected category
            try:
                category_id = self.data.get('category')
                self.fields['subcategories'].queryset = ServiceSubcategory.objects.filter(
                    category_id=category_id,
                    is_active=True
                )
            except (ValueError, TypeError):
                # Invalid category ID
                self.fields['subcategories'].queryset = ServiceSubcategory.objects.none()
        else:
            # For new services (GET request), queryset will be updated via JavaScript
            self.fields['subcategories'].queryset = ServiceSubcategory.objects.none()
