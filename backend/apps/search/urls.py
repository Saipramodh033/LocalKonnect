"""
URL patterns for search and discovery
"""

from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_results, name='results'),
    path('contractor/<uuid:contractor_id>/', views.contractor_detail, name='contractor_detail'),
]
