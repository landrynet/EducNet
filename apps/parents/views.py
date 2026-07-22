from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Parent
from .forms import ParentForm
from apps.authentication.decorators import role_required
from apps.audit.utils import log_action


@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def parent_list(request):
    school = request.user.school
    parents = Parent.objects.filter(school=school).prefetch_related('children') if school else Parent.objects.all()
    search = request.GET.get('q', '')
    if search:
        parents = parents.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(phone__icontains=search)
            | Q(email__icontains=search)
            | Q(children__first_name__icontains=search)
            | Q(children__last_name__icontains=search)
            | Q(children__student_id__icontains=search)
        ).distinct()
    paginator = Paginator(parents, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'parents/list.html', {'page_obj': page, 'search': search, 'title': 'Parents & Tuteurs'})


@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def parent_create(request):
    school = request.user.school
    if request.method == 'POST':
        form = ParentForm(request.POST, school=school)
        if form.is_valid():
            parent = form.save(commit=False)
            selected_children = form.cleaned_data.get('children')
            parent.school = school or (selected_children.first().school if selected_children else None)
            if parent.school is None:
                form.add_error('children', "Sélectionnez au moins un élève pour déterminer l'établissement.")
                return render(request, 'parents/form.html', {'form': form, 'title': 'Nouveau parent / tuteur'})
            parent.save()
            form.save_m2m()
            log_action(request.user, 'CREATE', f"Parent créé: {parent.get_full_name()}", parent)
            messages.success(request, "Parent enregistré.")
            return redirect('parents:list')
    else:
        form = ParentForm(school=school)
    return render(request, 'parents/form.html', {'form': form, 'title': 'Nouveau parent / tuteur'})


@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def parent_edit(request, pk):
    school = request.user.school
    parent = get_object_or_404(Parent, pk=pk, school=school) if school else get_object_or_404(Parent, pk=pk)
    if request.method == 'POST':
        form = ParentForm(request.POST, instance=parent, school=school)
        if form.is_valid():
            form.save()
            messages.success(request, "Parent modifié.")
            return redirect('parents:list')
    else:
        form = ParentForm(instance=parent, school=school)
    return render(request, 'parents/form.html', {'form': form, 'title': f'Modifier: {parent.get_full_name()}'})
