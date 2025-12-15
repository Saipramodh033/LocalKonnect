# Admin configuration for search
from django.contrib import admin
from .models import SearchRankingCache

admin.site.register(SearchRankingCache)
