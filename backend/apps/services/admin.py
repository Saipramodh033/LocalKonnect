# Admin configuration for services
from django.contrib import admin
from .models import ServiceCategory, ServiceSubcategory, ContractorService, ServicePortfolioItem

admin.site.register(ServiceCategory)
admin.site.register(ServiceSubcategory)
admin.site.register(ContractorService)
admin.site.register(ServicePortfolioItem)
