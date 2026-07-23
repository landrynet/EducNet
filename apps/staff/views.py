"""Staff management views."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from .models import StaffProfile
from .forms import StaffUserForm, StaffProfileForm
from apps.users.models import User
from apps.authentication.decorators import role_required
from apps.audit.utils import log_action


@login_required
@role_required(['admin_ecole', 'super_admin'])
def staff_list(request):
    school = request.user.school
    staff = (
        StaffProfile.objects.filter(school=school).select_related('user')
        if school else
        StaffProfile.objects.all().select_related('user', 'school')
    )
    # Search
    q = request.GET.get('q', '')
    if q:
        staff = staff.filter(
            user__first_name__icontains=q
        ) | staff.filter(
            user__last_name__icontains=q
        ) | staff.filter(
            employee_id__icontains=q
        )
        # Re-apply school filter after OR
        if school:
            staff = staff.filter(school=school)

    staff_type = request.GET.get('type', '')
    if staff_type:
        staff = staff.filter(staff_type=staff_type)

    paginator = Paginator(staff.distinct(), 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'staff/list.html', {
        'page_obj': page,
        'title': 'Personnel',
        'search': q,
        'staff_type': staff_type,
    })


@login_required
@role_required(['admin_ecole', 'super_admin'])
def staff_create(request):
    school = request.user.school
    if request.method == 'POST':
        user_form = StaffUserForm(request.POST)
        profile_form = StaffProfileForm(request.POST, school=school)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                # Create User
                user = user_form.save(commit=False)
                user.school = school
                user.must_change_password = True
                user.set_password(user_form.cleaned_data['password'])
                user.save()
                # Create StaffProfile
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.school = school
                profile.save()
                profile_form.save_m2m()  # save subjects M2M
                log_action(request.user, 'CREATE', f"Création personnel: {user.get_full_name()}", profile)
            messages.success(request, f"Membre du personnel «{user.get_full_name()}» créé avec succès.")
            return redirect('staff:list')
    else:
        user_form = StaffUserForm()
        profile_form = StaffProfileForm(school=school)
    return render(request, 'staff/form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Ajouter un membre du personnel',
        'action': 'Créer',
    })


@login_required
@role_required(['admin_ecole', 'super_admin'])
def staff_edit(request, pk):
    school = request.user.school
    profile = get_object_or_404(
        StaffProfile,
        pk=pk,
        **(({'school': school}) if school else {})
    )
    if request.method == 'POST':
        user_form = StaffUserForm(request.POST, instance=profile.user)
        profile_form = StaffProfileForm(request.POST, instance=profile, school=school)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user = user_form.save(commit=False)
                pwd = user_form.cleaned_data.get('password')
                if pwd:
                    user.set_password(pwd)
                user.save()
                profile_form.save()  # saves instance + M2M subjects
                log_action(request.user, 'UPDATE', f"Modification personnel: {user.get_full_name()}", profile)
            messages.success(request, "Informations du personnel mises à jour.")
            return redirect('staff:detail', pk=profile.pk)
    else:
        user_form = StaffUserForm(instance=profile.user)
        profile_form = StaffProfileForm(instance=profile, school=school)
    return render(request, 'staff/form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
        'title': f"Modifier: {profile.user.get_full_name()}",
        'action': 'Enregistrer',
    })


@login_required
@role_required(['admin_ecole', 'super_admin'])
def staff_detail(request, pk):
    school = request.user.school
    profile = get_object_or_404(
        StaffProfile,
        pk=pk,
        **(({'school': school}) if school else {})
    )
    return render(request, 'staff/detail.html', {
        'profile': profile,
        'title': profile.user.get_full_name(),
    })


@login_required
@role_required(['admin_ecole', 'super_admin'])
def staff_toggle(request, pk):
    school = request.user.school
    profile = get_object_or_404(
        StaffProfile,
        pk=pk,
        **(({'school': school}) if school else {})
    )
    profile.is_active = not profile.is_active
    profile.save()
    profile.user.is_active = profile.is_active
    profile.user.save()
    status = "activé" if profile.is_active else "désactivé"
    messages.success(request, f"Personnel {status}.")
    log_action(request.user, 'UPDATE', f"Toggle personnel: {profile.user.get_full_name()} → {status}", profile)
    return redirect('staff:list')
