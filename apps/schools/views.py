"""School management views — Super Admin only."""

import secrets
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import School
from .forms import SchoolForm, SchoolCreationForm
from apps.authentication.decorators import role_required
from apps.audit.utils import log_action
from apps.users.models import User, Role


def _temporary_password(length=12):
    alphabet = string.ascii_letters + string.digits + '!@#$%&*'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _admin_email_for_school(school):
    base = (school.email or '').strip().lower()
    if base and not User.objects.filter(email=base).exists():
        return base
    slug = ''.join(char.lower() if char.isalnum() else '.' for char in school.code).strip('.')
    candidate = f"admin.{slug}@edumanager.local"
    suffix = 2
    while User.objects.filter(email=candidate).exists():
        candidate = f"admin.{slug}{suffix}@edumanager.local"
        suffix += 1
    return candidate


@login_required
@role_required(['super_admin'])
def school_list(request):
    schools = School.objects.annotate(
        total_users=Count('users', distinct=True),
    )
    search = request.GET.get('q', '')
    if search:
        schools = schools.filter(Q(name__icontains=search) | Q(code__icontains=search))
    paginator = Paginator(schools, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'schools/list.html', {
        'page_obj': page,
        'search': search,
        'title': 'Gestion des écoles',
    })


@login_required
@role_required(['super_admin'])
def school_create(request):
    if request.method == 'POST':
        form = SchoolCreationForm(request.POST, request.FILES)
        if form.is_valid():
            school = form.save()
            login_email = _admin_email_for_school(school)
            temporary_password = _temporary_password()
            director_parts = (school.director_name or 'Responsable École').split()
            admin = User.objects.create(
                email=login_email,
                first_name=director_parts[0],
                last_name=' '.join(director_parts[1:]) or 'École',
                role=Role.ADMIN_ECOLE,
                school=school,
                phone=school.phone,
                must_change_password=True,
                profile_completed=False,
                is_active=True,
            )
            admin.set_password(temporary_password)
            admin.save(update_fields=['password'])
            log_action(request.user, 'CREATE', f"Création école: {school.name}", school)
            request.session['school_credentials'] = {
                'school_id': school.pk,
                'email': login_email,
                'temporary_password': temporary_password,
            }
            return redirect('schools:credentials', pk=school.pk)
    else:
        form = SchoolCreationForm()
    return render(request, 'schools/form.html', {
        'form': form,
        'title': 'Créer une école',
        'action': 'Créer',
    })


@login_required
@role_required(['super_admin'])
def school_edit(request, pk):
    school = get_object_or_404(School, pk=pk)
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            log_action(request.user, 'UPDATE', f"Modification école: {school.name}", school)
            messages.success(request, "École modifiée avec succès.")
            return redirect('schools:list')
    else:
        form = SchoolForm(instance=school)
    return render(request, 'schools/form.html', {
        'form': form,
        'title': f'Modifier: {school.name}',
        'action': 'Enregistrer',
    })


@login_required
@role_required(['super_admin'])
def school_detail(request, pk):
    school = get_object_or_404(School, pk=pk)
    responsible = school.users.filter(role=Role.ADMIN_ECOLE).order_by('date_joined').first()
    return render(request, 'schools/detail.html', {
        'school': school,
        'responsible': responsible,
        'title': school.name,
    })


@login_required
@role_required(['super_admin'])
def school_credentials(request, pk):
    school = get_object_or_404(School, pk=pk)
    credentials = request.session.get('school_credentials', {})
    if credentials.get('school_id') != school.pk:
        messages.error(request, "Ces identifiants temporaires ne sont plus disponibles.")
        return redirect('schools:detail', pk=school.pk)
    del request.session['school_credentials']
    return render(request, 'schools/credentials.html', {
        'school': school,
        'login_email': credentials['email'],
        'temporary_password': credentials['temporary_password'],
        'title': 'Accès initial de l’établissement',
    })


@login_required
@role_required(['admin_ecole'])
def school_settings(request):
    """Allow the school admin to update their own school's information."""
    school = request.user.school
    if not school:
        messages.error(request, "Votre compte n'est associé à aucun établissement.")
        return redirect('dashboard:index')
    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            log_action(request.user, 'UPDATE', f"Paramètres école modifiés: {school.name}", school)
            messages.success(request, "Paramètres enregistrés avec succès.")
            return redirect('schools:settings')
    else:
        form = SchoolForm(instance=school)
    return render(request, 'schools/settings.html', {
        'form': form,
        'school': school,
        'title': "Paramètres de l'établissement",
    })


@login_required
@role_required(['super_admin'])
def school_toggle(request, pk):
    school = get_object_or_404(School, pk=pk)
    school.is_active = not school.is_active
    school.save()
    status = "activée" if school.is_active else "désactivée"
    messages.success(request, f"École {status}.")
    return redirect('schools:list')
