"""Authentication views: login, logout, password change."""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import LoginForm, ChangePasswordForm
from apps.audit.utils import log_action
from apps.authentication.decorators import role_required
from apps.users.forms import ProfileForm
from apps.schools.forms import SchoolForm


def login_view(request):
    """Custom login view with email authentication."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Record IP address
            ip = request.META.get('REMOTE_ADDR')
            user.last_login_ip = ip
            user.save(update_fields=['last_login_ip'])
            log_action(user, 'LOGIN', f"Connexion depuis {ip}", user)
            messages.success(request, f"Bienvenue, {user.get_full_name()} !")
            next_url = request.GET.get('next')
            if not next_url:
                if user.must_change_password:
                    next_url = 'authentication:change_password'
                elif user.role == 'admin_ecole' and not user.profile_completed:
                    next_url = 'authentication:setup'
                else:
                    next_url = 'dashboard:index'
            return redirect(next_url)
        else:
            messages.error(request, "Email ou mot de passe incorrect.")
    else:
        form = LoginForm(request)

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    """Logout and redirect to login page."""
    if request.user.is_authenticated:
        log_action(request.user, 'LOGOUT', "Déconnexion", request.user)
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('authentication:login')


@login_required
def change_password(request):
    """Force password change on first login."""
    if not request.user.must_change_password:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            # SetPasswordForm validates the two new values. Set the password
            # explicitly here so the temporary credential is always replaced
            # before the first-login flow continues.
            from apps.users.models import User
            user_id = request.user.pk
            password_hash = make_password(form.cleaned_data['new_password1'])
            User.objects.filter(pk=user_id).update(
                password=password_hash,
                must_change_password=False,
            )
            request.session.pop('first_login_authenticated', None)
            user = User.objects.get(pk=user_id)
            update_session_auth_hash(request, user)
            log_action(user, 'UPDATE', "Changement de mot de passe", user)
            messages.success(request, "Mot de passe changé avec succès. Bienvenue !")
            if user.role == 'admin_ecole':
                return redirect('authentication:setup')
            return redirect('dashboard:index')
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'auth/change_password.html', {
        'form': form,
        'is_forced': request.user.must_change_password,
        'login_identifier': request.user.email,
    })


@login_required
@role_required(['admin_ecole'])
def setup(request):
    """Complete the school's first-time configuration in three steps."""
    step = request.GET.get('step', '1')
    if step not in {'1', '2', '3'}:
        step = '1'

    if step == '1':
        form = ProfileForm(request.POST or None, instance=request.user)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('/auth/setup/?step=2')
        return render(request, 'auth/setup.html', {
            'step': 1, 'form': form, 'title': 'Configuration initiale',
        })

    if not request.user.school:
        messages.error(request, "Votre compte n'est associé à aucune école.")
        return redirect('authentication:login')

    if step == '2':
        form = SchoolForm(
            request.POST or None,
            request.FILES or None,
            instance=request.user.school,
        )
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('/auth/setup/?step=3')
        return render(request, 'auth/setup.html', {
            'step': 2, 'form': form, 'title': 'Configuration initiale',
        })

    if request.method == 'POST':
        if not request.POST.get('tos_accepted'):
            messages.error(request, "Vous devez accepter les conditions d'utilisation pour continuer.")
            return render(request, 'auth/setup.html', {
                'step': 3,
                'school': request.user.school,
                'user_obj': request.user,
                'title': 'Vérification de la configuration',
            })
        request.user.profile_completed = True
        request.user.save(update_fields=['profile_completed'])
        log_action(request.user, 'UPDATE', "Configuration initiale terminée", request.user)
        messages.success(request, "Configuration terminée. Bienvenue dans votre espace !")
        return redirect('dashboard:index')

    return render(request, 'auth/setup.html', {
        'step': 3,
        'school': request.user.school,
        'user_obj': request.user,
        'title': 'Vérification de la configuration',
    })
