"""Student management views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Student
from .forms import StudentForm
from apps.authentication.decorators import role_required
from apps.audit.utils import log_action
import uuid


@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def student_list(request):
    school = request.user.school
    students = Student.objects.filter(school=school) if school else Student.objects.all()

    search = request.GET.get('q', '')
    status = request.GET.get('status', '')

    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(student_id__icontains=search)
        )
    if status == 'active':
        students = students.filter(is_active=True)
    elif status == 'inactive':
        students = students.filter(is_active=False)

    paginator = Paginator(students, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'students/list.html', {
        'page_obj': page,
        'search': search,
        'status': status,
        'title': 'Gestion des élèves',
    })


@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def student_create(request):
    school = request.user.school
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.school = school
            student.save()
            log_action(request.user, 'CREATE', f"Élève inscrit: {student.get_full_name()}", student)
            messages.success(request, f"Élève {student.get_full_name()} enregistré.")
            return redirect('students:list')
    else:
        form = StudentForm()
    return render(request, 'students/form.html', {
        'form': form,
        'title': 'Nouveau élève',
        'action': 'Enregistrer',
    })


@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def student_detail(request, pk):
    school = request.user.school
    student = get_object_or_404(Student, pk=pk, school=school) if school else get_object_or_404(Student, pk=pk)
    return render(request, 'students/detail.html', {
        'student': student,
        'title': student.get_full_name(),
    })


@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def student_edit(request, pk):
    school = request.user.school
    student = get_object_or_404(Student, pk=pk, school=school) if school else get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            log_action(request.user, 'UPDATE', f"Dossier élève modifié: {student.get_full_name()}", student)
            messages.success(request, "Dossier élève modifié.")
            return redirect('students:detail', pk=pk)
    else:
        form = StudentForm(instance=student)
    return render(request, 'students/form.html', {
        'form': form,
        'title': f'Modifier: {student.get_full_name()}',
        'student': student,
    })
