from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse


def rate_limit(key_func, limit: int, window_seconds: int):
    """Simple Redis-backed rate limit decorator.
    key_func(request) -> str unique key segment (e.g., ip+username)
    limit: max allowed hits per window
    window_seconds: window TTL in seconds
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            key_segment = key_func(request)
            key = f"rl:{view_func.__name__}:{key_segment}"
            # Increment counter atomically; set TTL on first hit
            count = cache.get(key)
            if count is None:
                cache.set(key, 1, timeout=window_seconds)
                count = 1
            else:
                cache.incr(key)
                count = int(count) + 1
            if count > limit:
                return JsonResponse(
                    {"detail": "Too many requests. Please try again later."},
                    status=429,
                )
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

def login_key_func(request):
    username = request.data.get('email') or request.POST.get('email') or ''
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR', '')
    return f"login:{ip}:{username}"
