from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from apps.authentication.decorators import role_required
from .models import ReportCard


@login_required
@role_required(['admin_ecole', 'enseignant', 'super_admin'])
def reports_index(request):
    school = request.user.school
    report_cards = ReportCard.objects.filter(school=school).select_related('student', 'period') if school else ReportCard.objects.all()
    paginator = Paginator(report_cards, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'reports/index.html', {'page_obj': page, 'title': 'Bulletins scolaires'})
