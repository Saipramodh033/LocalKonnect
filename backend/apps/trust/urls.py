"""
URL patterns for trust system
"""

from django.urls import path
from . import views

app_name = 'trust'

urlpatterns = [
    # Trust marks
    path('give/<uuid:service_id>/', views.give_trust_mark, name='give_trust_mark'),
    path('remove/<uuid:trust_mark_id>/', views.remove_trust_mark, name='remove_trust_mark'),
    path('verify/<uuid:trust_mark_id>/', views.verify_trust_mark, name='verify_trust_mark'),
    path('my-trust-marks/', views.my_trust_marks, name='my_trust_marks'),
    
    # Reviews
    path('review/add/<uuid:service_id>/', views.add_review, name='add_review'),
    path('review/helpful/<uuid:review_id>/', views.mark_review_helpful, name='mark_review_helpful'),
]
