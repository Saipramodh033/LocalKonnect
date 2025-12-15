# Admin configuration for trust system
from django.contrib import admin
from .models import TrustMark, Review, FraudPattern, TrustScoreHistory

admin.site.register(TrustMark)
admin.site.register(Review)
admin.site.register(FraudPattern)
admin.site.register(TrustScoreHistory)
