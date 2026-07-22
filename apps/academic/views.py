"""Academic organization views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.authentication.decorators import role_required, school_required
from .models import AcademicYear, Level, Classroom, Subject
from .forms import AcademicYearForm, LevelForm, ClassroomForm, SubjectForm
from apps.audit.utils import log_action


@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def index(request):
    school = request.user.school
    years = AcademicYear.objects.filter(school=school) if school else AcademicYear.objects.all()
    levels = Level.objects.filter(school=school) if school else Level.objects.all()
    subjects = Subject.objects.filter(school=school) if school else Subject.objects.all()
    classrooms = Classroom.objects.filter(school=school).select_related('level', 'academic_year') if school else Classroom.objects.none()
    return render(request, 'academic/index.html', {
        'years': years,
        'levels': levels,
        'subjects': subjects,
        'classrooms': classrooms,
        'title': 'Organisation académique',
    })


@login_required
@role_required(['admin_ecole', 'super_admin'])
def years(request):
    school = request.user.school
    qs = AcademicYear.objects.filter(school=school) if school else AcademicYear.objects.all()
    return render(request, 'academic/years.html', {
        'years': qs,
        'title': 'Années scolaires',
    })


@login_required
@role_required(['admin_ecole', 'super_admin'])
def year_create(request):
    school = request.user.school
    if request.method == 'POST':
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            year = form.save(commit=False)
            year.school = school
            year.save()
            log_action(request.user, 'CREATE', f"Année scolaire créée: {year.name}", year)
            messages.success(request, f"Année scolaire {year.name} créée.")
            return redirect('academic:years')
    else:
        form = AcademicYearForm()
    return render(request, 'academic/year_form.html', {'form': form, 'title': 'Nouvelle année scolaire'})


@login_required
@role_required(['admin_ecole', 'super_admin'])
def classroom_create(request):
    school = request.user.school
    if request.method == 'POST':
        form = ClassroomForm(request.POST, school=school)
        if form.is_valid():
            cls = form.save(commit=False)
            cls.school = school
            cls.save()
            messages.success(request, f"Classe {cls.name} créée.")
            return redirect('academic:index')
    else:
        form = ClassroomForm(school=school)
    return render(request, 'academic/classroom_form.html', {'form': form, 'title': 'Nouvelle classe'})


@login_required
@role_required(['admin_ecole', 'super_admin'])
def subject_create(request):
    school = request.user.school
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subj = form.save(commit=False)
            subj.school = school
            subj.save()
            messages.success(request, f"Matière {subj.name} créée.")
            return redirect('academic:index')
    else:
        form = SubjectForm()
    return render(request, 'academic/subject_form.html', {'form': form, 'title': 'Nouvelle matière'})
