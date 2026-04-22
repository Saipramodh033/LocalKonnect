# Admin configuration for trust system
from django.contrib import admin
from .models import Feedback, TrustScoreHistory

admin.site.register(Feedback)
admin.site.register(TrustScoreHistory)
