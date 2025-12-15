# Admin configuration for admin panel
from django.contrib import admin
from .models import AdminAction

admin.site.register(AdminAction)
