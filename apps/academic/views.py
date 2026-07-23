"""Academic organization views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.authentication.decorators import role_required
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
    classrooms = (
        Classroom.objects.filter(school=school)
        .select_related('level', 'academic_year')
        .prefetch_related('subjects')
        if school else Classroom.objects.none()
    )
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
            form.save_m2m()  # save subjects M2M
            log_action(request.user, 'CREATE', f"Classe créée: {cls.name}", cls)
            messages.success(request, f"Classe {cls.name} créée.")
            return redirect('academic:classroom_detail', pk=cls.pk)
    else:
        form = ClassroomForm(school=school)
    return render(request, 'academic/classroom_form.html', {'form': form, 'title': 'Nouvelle classe'})


@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def classroom_detail(request, pk):
    school = request.user.school
    cls = get_object_or_404(
        Classroom,
        pk=pk,
        **(({'school': school}) if school else {})
    )
    school_subjects = Subject.objects.filter(school=cls.school)
    assigned_ids = set(cls.subjects.values_list('id', flat=True))

    # Staff members (teachers) of this school with their subject assignments
    from apps.staff.models import StaffProfile
    teachers = (
        StaffProfile.objects.filter(school=cls.school, staff_type='teacher')
        .select_related('user')
        .prefetch_related('subjects')
    )

    return render(request, 'academic/classroom_detail.html', {
        'cls': cls,
        'school_subjects': school_subjects,
        'assigned_ids': assigned_ids,
        'teachers': teachers,
        'title': cls.name,
    })


@login_required
@role_required(['admin_ecole', 'super_admin'])
def classroom_edit(request, pk):
    school = request.user.school
    cls = get_object_or_404(
        Classroom,
        pk=pk,
        **(({'school': school}) if school else {})
    )
    if request.method == 'POST':
        form = ClassroomForm(request.POST, instance=cls, school=school)
        if form.is_valid():
            form.save()  # saves both instance and M2M subjects
            log_action(request.user, 'UPDATE', f"Classe modifiée: {cls.name}", cls)
            messages.success(request, f"Classe {cls.name} mise à jour.")
            return redirect('academic:classroom_detail', pk=cls.pk)
    else:
        form = ClassroomForm(instance=cls, school=school)
    return render(request, 'academic/classroom_form.html', {
        'form': form,
        'cls': cls,
        'title': f"Modifier: {cls.name}",
    })


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
            log_action(request.user, 'CREATE', f"Matière créée: {subj.name}", subj)
            messages.success(request, f"Matière {subj.name} créée.")
            return redirect('academic:index')
    else:
        form = SubjectForm()
    return render(request, 'academic/subject_form.html', {'form': form, 'title': 'Nouvelle matière'})


@login_required
@role_required(['admin_ecole', 'super_admin'])
def subject_edit(request, pk):
    school = request.user.school
    subj = get_object_or_404(
        Subject,
        pk=pk,
        **(({'school': school}) if school else {})
    )
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subj)
        if form.is_valid():
            form.save()
            log_action(request.user, 'UPDATE', f"Matière modifiée: {subj.name}", subj)
            messages.success(request, f"Matière {subj.name} mise à jour.")
            return redirect('academic:index')
    else:
        form = SubjectForm(instance=subj)
    return render(request, 'academic/subject_form.html', {
        'form': form,
        'subj': subj,
        'title': f"Modifier: {subj.name}",
    })
