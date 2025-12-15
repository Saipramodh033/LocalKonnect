from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse
from apps.contractors.models import ContractorProfile


def require_contractor_profile(view_func):
    """Ensure the user is a contractor and has a ContractorProfile."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or getattr(user, 'user_type', None) != 'contractor':
            return redirect(reverse('users:login'))
        if not ContractorProfile.objects.filter(user=user).exists():
            return redirect(reverse('contractors:profile'))
        return view_func(request, *args, **kwargs)
    return _wrapped
