"""Role-based dashboard views."""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone


@login_required
def index(request):
    """Route to appropriate dashboard based on user role."""
    role = request.user.role
    if role == 'super_admin':
        return super_admin_dashboard(request)
    elif role == 'admin_ecole':
        return admin_ecole_dashboard(request)
    elif role == 'secretaire':
        return secretaire_dashboard(request)
    elif role == 'enseignant':
        return enseignant_dashboard(request)
    elif role == 'comptable':
        return comptable_dashboard(request)
    return render(request, 'dashboard/index.html', {'title': 'Tableau de bord'})


def super_admin_dashboard(request):
    from apps.schools.models import School
    from apps.users.models import User

    stats = {
        'total_schools': School.objects.count(),
        'active_schools': School.objects.filter(is_active=True).count(),
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
    }
    recent_schools = School.objects.order_by('-created_at')[:5]
    return render(request, 'dashboard/super_admin.html', {
        'stats': stats,
        'recent_schools': recent_schools,
        'title': 'Super Administration',
    })


def admin_ecole_dashboard(request):
    school = request.user.school
    from apps.users.models import User

    stats = {
        'total_users': User.objects.filter(school=school).count(),
        'total_students': 0,
        'active_year': None,
    }
    try:
        from apps.students.models import Student
        stats['total_students'] = Student.objects.filter(school=school, is_active=True).count()
    except Exception:
        pass
    try:
        from apps.academic.models import AcademicYear
        stats['active_year'] = AcademicYear.objects.filter(school=school, is_current=True).first()
    except Exception:
        pass
    return render(request, 'dashboard/admin_ecole.html', {
        'stats': stats,
        'school': school,
        'title': "Administration — " + (school.name if school else ""),
    })


def secretaire_dashboard(request):
    school = request.user.school
    stats = {}
    try:
        from apps.students.models import Student
        stats['total_students'] = Student.objects.filter(school=school, is_active=True).count()
    except Exception:
        stats['total_students'] = 0
    try:
        from apps.enrollment.models import Enrollment
        stats['pending_enrollments'] = Enrollment.objects.filter(school=school, status='pending').count()
    except Exception:
        stats['pending_enrollments'] = 0
    return render(request, 'dashboard/secretaire.html', {
        'stats': stats,
        'title': 'Secrétariat',
    })


def enseignant_dashboard(request):
    school = request.user.school
    return render(request, 'dashboard/enseignant.html', {
        'title': 'Espace Enseignant',
        'school': school,
    })


def comptable_dashboard(request):
    school = request.user.school
    stats = {}
    try:
        from apps.finance.models import Payment
        stats['total_collected'] = Payment.objects.filter(
            school=school, status='paid'
        ).aggregate(total=Sum('amount'))['total'] or 0
        stats['pending_payments'] = Payment.objects.filter(school=school, status='pending').count()
    except Exception:
        stats['total_collected'] = 0
        stats['pending_payments'] = 0
    return render(request, 'dashboard/comptable.html', {
        'stats': stats,
        'title': 'Finance & Comptabilité',
    })
