from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg
from apps.authentication.decorators import role_required


@login_required
@role_required(['admin_ecole', 'comptable', 'super_admin'])
def analytics_index(request):
    school = request.user.school
    stats = {}
    try:
        from apps.students.models import Student
        stats['students_by_gender'] = Student.objects.filter(school=school).values('gender').annotate(count=Count('id'))
    except Exception:
        stats['students_by_gender'] = []
    try:
        from apps.finance.models import Payment
        stats['revenue_total'] = Payment.objects.filter(school=school, status='paid').aggregate(total=Sum('amount'))['total'] or 0
    except Exception:
        stats['revenue_total'] = 0
    try:
        from apps.assessments.models import Grade
        stats['avg_grade'] = Grade.objects.filter(
            assessment__school=school
        ).aggregate(avg=Avg('score'))['avg'] or 0
    except Exception:
        stats['avg_grade'] = 0
    return render(request, 'analytics/index.html', {'stats': stats, 'title': 'Rapports & Statistiques'})
