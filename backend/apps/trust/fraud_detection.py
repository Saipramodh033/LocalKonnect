"""
Fraud detection algorithms
"""

from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
from apps.trust.models import TrustMark, FraudPattern
from apps.users.models import User
import logging

logger = logging.getLogger(__name__)


def detect_rapid_trust_bursts(time_window_hours=1, threshold=5):
    """
    Detect rapid bursts of trust marks from same IP or user.
    
    Args:
        time_window_hours: Time window to check
        threshold: Number of trusts to flag as burst
    
    Returns:
        list: Detected fraud patterns
    """
    since = timezone.now() - timedelta(hours=time_window_hours)
    patterns = []
    
    # Group by IP address
    trust_marks = TrustMark.objects.filter(
        created_at__gte=since,
        status='active'
    ).values('ip_address').annotate(
        count=Count('id')
    ).filter(count__gte=threshold)
    
    for item in trust_marks:
        if item['ip_address']:
            # Create fraud pattern
            pattern = FraudPattern.objects.create(
                pattern_type='rapid_burst',
                severity='high' if item['count'] > threshold * 2 else 'medium',
                description=f"Rapid trust burst detected: {item['count']} trusts from IP {item['ip_address']} in {time_window_hours}h",
                confidence_score=min(item['count'] / (threshold * 2), 1.0),
                evidence={'ip': item['ip_address'], 'count': item['count'], 'hours': time_window_hours}
            )
            
            # Link affected trust marks
            affected = TrustMark.objects.filter(
                ip_address=item['ip_address'],
                created_at__gte=since
            )
            pattern.affected_trust_marks.set(affected)
            patterns.append(pattern)
    
    return patterns


def detect_identical_reviews(similarity_threshold=0.9):
    """
    Detect identical or very similar review texts.
    
    Args:
        similarity_threshold: Text similarity threshold (0-1)
    
    Returns:
        list: Detected fraud patterns
    """
    from apps.trust.models import Review
    import difflib
    
    patterns = []
    recent_reviews = Review.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).exclude(text='')
    
    reviewed_pairs = set()
    
    for i, review1 in enumerate(recent_reviews):
        for review2 in recent_reviews[i+1:]:
            pair_key = tuple(sorted([review1.id, review2.id]))
            
            if pair_key in reviewed_pairs:
                continue
            
            reviewed_pairs.add(pair_key)
            
            # Calculate similarity
            similarity = difflib.SequenceMatcher(
                None,
                review1.text.lower(),
                review2.text.lower()
            ).ratio()
            
            if similarity >= similarity_threshold:
                # Create fraud pattern
                pattern = FraudPattern.objects.create(
                    pattern_type='identical_text',
                    severity='medium',
                    description=f"Identical review text detected ({similarity:.2%} similar)",
                    confidence_score=similarity,
                    evidence={
                        'review1_id': str(review1.id),
                        'review2_id': str(review2.id),
                        'similarity': similarity
                    }
                )
                
                pattern.affected_users.set([review1.customer, review2.customer])
                patterns.append(pattern)
    
    return patterns


def detect_ip_clustering():
    """
    Detect suspicious IP address clustering patterns.
    
    Returns:
        list: Detected fraud patterns
    """
    patterns = []
    recent_window = timezone.now() - timedelta(days=7)
    
    # Find IPs with multiple users
    ip_users = defaultdict(set)
    
    trust_marks = TrustMark.objects.filter(
        created_at__gte=recent_window
    ).select_related('customer')
    
    for tm in trust_marks:
        if tm.ip_address:
            ip_users[tm.ip_address].add(tm.customer.id)
    
    # Flag IPs with 3+ different users
    for ip, users in ip_users.items():
        if len(users) >= 3:
            pattern = FraudPattern.objects.create(
                pattern_type='ip_cluster',
                severity='medium',
                description=f"IP clustering detected: {len(users)} users from IP {ip}",
                confidence_score=min(len(users) / 10, 1.0),
                evidence={'ip': ip, 'user_count': len(users)}
            )
            
            affected_users = User.objects.filter(id__in=users)
            pattern.affected_users.set(affected_users)
            patterns.append(pattern)
    
    return patterns


def detect_coordinated_attacks():
    """
    Detect coordinated attacks on contractor services.
    
    Returns:
        list: Detected fraud patterns
    """
    patterns = []
    recent_window = timezone.now() - timedelta(hours=24)
    
    from apps.services.models import ContractorService
    
    # Find services with unusual trust mark spikes
    for service in ContractorService.objects.all():
        recent_trusts = TrustMark.objects.filter(
            contractor_service=service,
            created_at__gte=recent_window,
            status='active'
        )
        
        if recent_trusts.count() >= 10:  # 10+ trusts in 24h is suspicious
            # Check if from different users
            unique_users = recent_trusts.values('customer').distinct().count()
            
            if unique_users < recent_trusts.count() * 0.5:  # Less than 50% unique users
                pattern = FraudPattern.objects.create(
                    pattern_type='coordinated_attack',
                    severity='critical',
                    description=f"Coordinated attack detected on {service.contractor.business_name}",
                    confidence_score=0.85,
                    evidence={
                        'total_trusts': recent_trusts.count(),
                        'unique_users': unique_users,
                        'service_id': str(service.id)
                    },
                    affected_contractor_service=service
                )
                
                pattern.affected_trust_marks.set(recent_trusts)
                patterns.append(pattern)
    
    return patterns
