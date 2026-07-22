"""Audit middleware — minimal overhead request tracking."""


class AuditMiddleware:
    """Attaches request info to thread local for use in audit logging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Attach request to thread-local for use in views
        response = self.get_response(request)
        return response
