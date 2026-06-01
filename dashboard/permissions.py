from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps


def require_auth(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/?next=' + request.path)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/login/?next=' + request.path)
            if not hasattr(request.user, 'role') or request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator