from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.authentication.decorators import role_required


@login_required
@role_required(['admin_ecole', 'secretaire', 'enseignant', 'super_admin'])
def timetable_index(request):
    school = request.user.school
    entries = []
    try:
        from .models import TimetableEntry
        entries = TimetableEntry.objects.filter(school=school).select_related(
            'classroom', 'subject', 'teacher', 'timeslot'
        ) if school else []
    except Exception:
        pass
    return render(request, 'timetable/index.html', {
        'entries': entries,
        'title': 'Emplois du temps',
    })
