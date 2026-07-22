from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.core.paginator import Paginator
from apps.authentication.decorators import role_required
from .models import Announcement, Message
from django import forms


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'priority', 'target_audience', 'expires_at']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


@login_required
def communication_index(request):
    school = request.user.school
    announcements = Announcement.objects.filter(school=school, is_published=True) if school else Announcement.objects.none()
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.school = school
            announcement.author = request.user
            announcement.save()
            django_messages.success(request, "Annonce publiée.")
            return redirect('communication:index')
    else:
        form = AnnouncementForm()
    paginator = Paginator(announcements, 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'communication/index.html', {
        'page_obj': page,
        'form': form,
        'title': 'Communication',
    })
