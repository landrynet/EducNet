"""User management views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import User, Role
from .forms import UserCreateForm, UserEditForm, ProfileForm
from apps.authentication.decorators import role_required
from apps.audit.utils import log_action


@login_required
@role_required(['super_admin', 'admin_ecole'])
def user_list(request):
    """List users scoped to current school or all for super admin."""
    if request.user.is_super_admin:
        # Platform support needs school contacts, not every personal account.
        users = User.objects.select_related('school').filter(role='admin_ecole')
    else:
        users = User.objects.filter(school=request.user.school)

    search = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')

    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    if role_filter:
        users = users.filter(role=role_filter)

    paginator = Paginator(users, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'users/list.html', {
        'page_obj': page,
        'search': search,
        'role_filter': role_filter,
        'roles': Role.choices,
        'title': 'Gestion des utilisateurs',
    })


@login_required
@role_required(['super_admin', 'admin_ecole'])
def user_create(request):
    """Create a new user."""
    school = None if request.user.is_super_admin else request.user.school

    if request.method == 'POST':
        form = UserCreateForm(request.POST, request.FILES, school=school, current_user=request.user)
        if form.is_valid():
            user = form.save()
            log_action(request.user, 'CREATE', f"Création utilisateur: {user.get_full_name()}", user)
            messages.success(request, f"Utilisateur {user.get_full_name()} créé avec succès.")
            return redirect('users:list')
    else:
        form = UserCreateForm(school=school, current_user=request.user)

    return render(request, 'users/form.html', {
        'form': form,
        'title': 'Créer un utilisateur',
        'action': 'Créer',
    })


@login_required
@role_required(['super_admin', 'admin_ecole'])
def user_edit(request, pk):
    """Edit a user."""
    if request.user.is_super_admin:
        user = get_object_or_404(User, pk=pk)
    else:
        user = get_object_or_404(User, pk=pk, school=request.user.school)

    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            log_action(request.user, 'UPDATE', f"Modification utilisateur: {user.get_full_name()}", user)
            messages.success(request, "Utilisateur modifié avec succès.")
            return redirect('users:list')
    else:
        form = UserEditForm(instance=user)

    return render(request, 'users/form.html', {
        'form': form,
        'title': f'Modifier: {user.get_full_name()}',
        'action': 'Enregistrer',
        'user_obj': user,
    })


@login_required
@role_required(['super_admin', 'admin_ecole'])
def user_toggle_active(request, pk):
    """Activate or deactivate a user."""
    if request.user.is_super_admin:
        user = get_object_or_404(User, pk=pk)
    else:
        user = get_object_or_404(User, pk=pk, school=request.user.school)

    user.is_active = not user.is_active
    user.save()
    status = "activé" if user.is_active else "désactivé"
    log_action(request.user, 'UPDATE', f"Utilisateur {status}: {user.get_full_name()}", user)
    messages.success(request, f"Utilisateur {status}.")
    return redirect('users:list')


@login_required
@role_required(['super_admin', 'admin_ecole'])
def user_detail(request, pk):
    """View a user's detail page (read-only)."""
    if request.user.is_super_admin:
        user_obj = get_object_or_404(User, pk=pk)
    else:
        user_obj = get_object_or_404(User, pk=pk, school=request.user.school)

    # Try to get associated staff profile if the user is a teacher
    staff_profile = None
    try:
        staff_profile = user_obj.staff_profile
    except Exception:
        pass

    return render(request, 'users/detail.html', {
        'user_obj': user_obj,
        'staff_profile': staff_profile,
        'title': user_obj.get_full_name(),
    })


@login_required
def profile(request):
    """User's own profile."""
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.profile_completed = True
            user.save()
            messages.success(request, "Profil mis à jour.")
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'users/profile.html', {
        'form': form,
        'title': 'Mon profil',
    })
