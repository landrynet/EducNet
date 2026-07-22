from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from apps.authentication.decorators import role_required
from .models import Route, StudentTransport


@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def transport_index(request):
    school = request.user.school
    routes = Route.objects.filter(school=school) if school else Route.objects.all()
    return render(request, 'transport/index.html', {'routes': routes, 'title': 'Transport scolaire'})
