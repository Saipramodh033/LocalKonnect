# Admin configuration for contractors
from django.contrib import admin
from .models import ContractorProfile, ContractorDispute, ContractorAnalytics

admin.site.register(ContractorProfile)
admin.site.register(ContractorDispute)
admin.site.register(ContractorAnalytics)
