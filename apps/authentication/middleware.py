"""Authentication middleware for first-login enforcement."""

from django.shortcuts import redirect
from django.urls import reverse


class FirstLoginMiddleware:
    """
    Redirect authenticated users who must change their password
    to the password-change page before accessing anything else.
    """
    EXEMPT_URLS = [
        '/auth/login/',
        '/auth/logout/',
        '/auth/change-password/',
        '/static/',
        '/media/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.must_change_password:
            current = request.path
            exempt = any(current.startswith(url) for url in self.EXEMPT_URLS)
            if not exempt:
                return redirect(reverse('authentication:change_password'))
        return self.get_response(request)
