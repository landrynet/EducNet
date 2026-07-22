from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from apps.authentication.decorators import role_required
from .models import AuditLog, AuditAction


@login_required
@role_required(['super_admin', 'admin_ecole'])
def audit_list(request):
    if request.user.is_super_admin:
        logs = AuditLog.objects.select_related('user', 'school').all()
    else:
        logs = AuditLog.objects.filter(school=request.user.school).select_related('user')

    action_filter = request.GET.get('action', '')
    search = request.GET.get('q', '')

    if action_filter:
        logs = logs.filter(action=action_filter)
    if search:
        logs = logs.filter(
            Q(description__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )

    paginator = Paginator(logs, 30)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'audit/list.html', {
        'page_obj': page,
        'action_filter': action_filter,
        'search': search,
        'actions': AuditAction.choices,
        'title': "Journal d'audit",
    })
