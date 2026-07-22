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

    schools = School.objects.all()
    users = User.objects.all()

    stats = {
        'total_schools': schools.count(),
        'active_schools': schools.filter(is_active=True).count(),
        'inactive_schools': schools.filter(is_active=False).count(),
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
    }

    # Users by role breakdown
    role_counts = users.values('role').annotate(count=Count('id'))
    stats['role_breakdown'] = {r['role']: r['count'] for r in role_counts}

    recent_schools = schools.order_by('-created_at')[:5]
    recent_users = users.order_by('-date_joined')[:5]

    return render(request, 'dashboard/super_admin.html', {
        'stats': stats,
        'recent_schools': recent_schools,
        'recent_users': recent_users,
        'title': 'Super Administration',
    })


def admin_ecole_dashboard(request):
    school = request.user.school
    from apps.users.models import User

    stats = {
        'total_users': User.objects.filter(school=school).count(),
        'active_users': User.objects.filter(school=school, is_active=True).count(),
        'total_students': 0,
        'active_students': 0,
        'total_staff': 0,
        'active_staff': 0,
        'total_subjects': 0,
        'pending_enrollments': 0,
        'active_year': None,
    }

    try:
        from apps.students.models import Student
        students = Student.objects.filter(school=school)
        stats['total_students'] = students.count()
        stats['active_students'] = students.filter(is_active=True).count()
    except Exception:
        pass

    try:
        from apps.staff.models import StaffProfile
        staff = StaffProfile.objects.filter(school=school)
        stats['total_staff'] = staff.count()
        stats['active_staff'] = staff.filter(is_active=True).count()
    except Exception:
        pass

    try:
        from apps.academic.models import AcademicYear, Subject
        stats['active_year'] = AcademicYear.objects.filter(school=school, is_current=True).first()
        stats['total_subjects'] = Subject.objects.filter(school=school).count()
    except Exception:
        pass

    try:
        from apps.enrollment.models import Enrollment
        stats['pending_enrollments'] = Enrollment.objects.filter(school=school, status='pending').count()
    except Exception:
        pass

    return render(request, 'dashboard/admin_ecole.html', {
        'stats': stats,
        'school': school,
        'title': "Tableau de bord — " + (school.name if school else ""),
    })


def secretaire_dashboard(request):
    school = request.user.school
    stats = {
        'total_students': 0,
        'active_students': 0,
        'pending_enrollments': 0,
        'total_enrollments': 0,
    }
    try:
        from apps.students.models import Student
        students = Student.objects.filter(school=school)
        stats['total_students'] = students.count()
        stats['active_students'] = students.filter(is_active=True).count()
    except Exception:
        pass
    try:
        from apps.enrollment.models import Enrollment
        enrollments = Enrollment.objects.filter(school=school)
        stats['total_enrollments'] = enrollments.count()
        stats['pending_enrollments'] = enrollments.filter(status='pending').count()
    except Exception:
        pass
    return render(request, 'dashboard/secretaire.html', {
        'stats': stats,
        'title': 'Secrétariat',
    })


def enseignant_dashboard(request):
    school = request.user.school
    stats = {
        'my_subjects': 0,
        'timetable_entries': 0,
    }
    try:
        from apps.staff.models import StaffProfile
        profile = StaffProfile.objects.filter(user=request.user).first()
        if profile:
            stats['my_subjects'] = profile.subjects.count()
    except Exception:
        pass
    try:
        from apps.timetable.models import TimetableEntry
        stats['timetable_entries'] = TimetableEntry.objects.filter(
            school=school, teacher=request.user
        ).count()
    except Exception:
        pass
    return render(request, 'dashboard/enseignant.html', {
        'title': 'Espace Enseignant',
        'school': school,
        'stats': stats,
    })


def comptable_dashboard(request):
    school = request.user.school
    stats = {
        'total_collected': 0,
        'pending_payments': 0,
        'total_payments': 0,
        'overdue_payments': 0,
    }
    try:
        from apps.finance.models import Payment
        payments = Payment.objects.filter(school=school)
        stats['total_collected'] = payments.filter(status='paid').aggregate(
            total=Sum('amount'))['total'] or 0
        stats['pending_payments'] = payments.filter(status='pending').count()
        stats['total_payments'] = payments.count()
        stats['overdue_payments'] = payments.filter(status='overdue').count()
    except Exception:
        pass
    return render(request, 'dashboard/comptable.html', {
        'stats': stats,
        'title': 'Finance & Comptabilité',
    })
