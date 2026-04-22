"""
URL patterns for trust system
"""

from django.urls import path
from . import views

app_name = 'trust'

urlpatterns = [
    path('feedback/<uuid:service_id>/', views.submit_feedback, name='submit_feedback'),
    path('my-feedback/', views.my_feedback, name='my_feedback'),
]
