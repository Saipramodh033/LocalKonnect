"""Customer URL Configuration"""
from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    path('dashboard/', views.customer_dashboard, name='dashboard'),
    path('profile/', views.customer_profile, name='profile'),
    path('saved/', views.customer_saved_contractors, name='saved_contractors'),
]
