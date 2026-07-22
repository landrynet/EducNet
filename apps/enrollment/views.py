from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Enrollment
from apps.authentication.decorators import role_required
from apps.audit.utils import log_action
from django import forms


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'classroom', 'academic_year', 'status', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            from apps.students.models import Student
            from apps.academic.models import Classroom, AcademicYear
            self.fields['student'].queryset = Student.objects.filter(school=school, is_active=True)
            self.fields['classroom'].queryset = Classroom.objects.filter(school=school)
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(school=school)


@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def enrollment_index(request):
    school = request.user.school
    enrollments = Enrollment.objects.filter(school=school).select_related('student', 'classroom', 'academic_year') if school else Enrollment.objects.all()
    paginator = Paginator(enrollments, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'enrollment/index.html', {'page_obj': page, 'title': 'Inscriptions'})


@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def enrollment_create(request):
    school = request.user.school
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, school=school)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.school = school
            enrollment.save()
            log_action(request.user, 'CREATE', f"Inscription: {enrollment.student}", enrollment)
            messages.success(request, "Élève inscrit avec succès.")
            return redirect('enrollment:index')
    else:
        form = EnrollmentForm(school=school)
    return render(request, 'enrollment/form.html', {'form': form, 'title': 'Nouvelle inscription'})
