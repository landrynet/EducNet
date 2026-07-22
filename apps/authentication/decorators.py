"""Decorators for role-based access control."""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles):
    """
    Decorator that restricts view access to users with specific roles.
    Usage: @role_required(['admin_ecole', 'secretaire'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('authentication:login')
            if request.user.role not in allowed_roles:
                messages.error(request, "Accès non autorisé. Vous n'avez pas les permissions nécessaires.")
                return redirect('dashboard:index')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def school_required(view_func):
    """Ensure user belongs to a school (not applicable to super admin)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('authentication:login')
        if not request.user.is_super_admin and not request.user.school:
            messages.error(request, "Aucune école associée à votre compte.")
            return redirect('authentication:login')
        return view_func(request, *args, **kwargs)
    return wrapper
