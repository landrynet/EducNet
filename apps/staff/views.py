from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import StaffProfile
from apps.authentication.decorators import role_required


@login_required
@role_required(['admin_ecole', 'super_admin'])
def staff_list(request):
    school = request.user.school
    staff = StaffProfile.objects.filter(school=school).select_related('user') if school else StaffProfile.objects.all()
    paginator = Paginator(staff, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'staff/list.html', {'page_obj': page, 'title': 'Personnel'})
