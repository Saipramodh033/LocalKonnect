"""
Admin panel models for moderation
"""

from django.db import models
from apps.users.models import User
from apps.trust.models import TrustMark, FraudPattern
from apps.contractors.models import ContractorDispute
import uuid


class AdminAction(models.Model):
    """Track admin actions for audit trail"""
    
    ACTION_TYPES = (
        ('approve_trust', 'Approve Trust Mark'),
        ('remove_trust', 'Remove Trust Mark'),
        ('ban_user', 'Ban User'),
        ('unban_user', 'Unban User'),
        ('verify_contractor', 'Verify Contractor'),
        ('reject_verification', 'Reject Verification'),
        ('resolve_dispute', 'Resolve Dispute'),
        ('flag_fraud', 'Flag Fraud'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_actions'
    )
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_actions_received'
    )
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_actions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action_type} by {self.admin_user} at {self.created_at}"
