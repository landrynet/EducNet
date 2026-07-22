"""Utility functions for recording audit log entries."""

from django.contrib.contenttypes.models import ContentType


def log_action(user, action, description, obj=None, request=None):
    """
    Record an action in the audit log.
    Safe to call even if audit tables don't exist yet (e.g., during migrations).
    """
    try:
        from .models import AuditLog
        kwargs = {
            'user': user,
            'action': action,
            'description': description,
        }
        if user and hasattr(user, 'school'):
            kwargs['school'] = user.school
        if obj is not None:
            try:
                ct = ContentType.objects.get_for_model(obj)
                kwargs['content_type'] = ct
                kwargs['object_id'] = obj.pk
            except Exception:
                pass
        if request:
            kwargs['ip_address'] = request.META.get('REMOTE_ADDR')
            kwargs['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:300]
        AuditLog.objects.create(**kwargs)
    except Exception:
        # Never crash the application because of audit logging
        pass
