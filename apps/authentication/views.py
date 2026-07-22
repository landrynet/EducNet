"""Authentication views: login, logout, password change."""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import LoginForm, ChangePasswordForm
from apps.audit.utils import log_action


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
            next_url = request.GET.get('next', 'dashboard:index')
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
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.must_change_password = False
            user.save(update_fields=['must_change_password'])
            update_session_auth_hash(request, user)
            log_action(user, 'UPDATE', "Changement de mot de passe", user)
            messages.success(request, "Mot de passe changé avec succès. Bienvenue !")
            return redirect('dashboard:index')
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'auth/change_password.html', {
        'form': form,
        'is_forced': request.user.must_change_password,
    })
