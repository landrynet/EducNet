"""School management views — Super Admin only."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import School
from .forms import SchoolForm
from apps.authentication.decorators import role_required
from apps.audit.utils import log_action


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
        form = SchoolForm(request.POST, request.FILES)
        if form.is_valid():
            school = form.save()
            log_action(request.user, 'CREATE', f"Création école: {school.name}", school)
            messages.success(request, f"École «{school.name}» créée avec succès.")
            return redirect('schools:list')
    else:
        form = SchoolForm()
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
    users = school.users.all().order_by('role', 'last_name')
    return render(request, 'schools/detail.html', {
        'school': school,
        'users': users,
        'title': school.name,
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
