from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from apps.authentication.decorators import role_required
from .models import Assessment, Grade
from apps.audit.utils import log_action
from django import forms


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ['classroom', 'subject', 'period', 'assessment_type', 'title', 'date', 'max_score', 'coefficient', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, school=None, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            from apps.academic.models import Classroom, Subject, Period
            self.fields['classroom'].queryset = Classroom.objects.filter(school=school)
            self.fields['subject'].queryset = Subject.objects.filter(school=school)
            self.fields['period'].queryset = Period.objects.filter(school=school)


@login_required
@role_required(['admin_ecole', 'enseignant', 'super_admin'])
def assessment_index(request):
    school = request.user.school
    assessments = Assessment.objects.filter(school=school).select_related('classroom', 'subject') if school else Assessment.objects.all()
    if request.user.is_enseignant:
        assessments = assessments.filter(teacher=request.user)
    paginator = Paginator(assessments, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'assessments/index.html', {'page_obj': page, 'title': 'Évaluations'})


@login_required
@role_required(['admin_ecole', 'enseignant', 'super_admin'])
def assessment_create(request):
    school = request.user.school
    if request.method == 'POST':
        form = AssessmentForm(request.POST, school=school)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.school = school
            assessment.teacher = request.user
            assessment.save()
            messages.success(request, "Évaluation créée.")
            return redirect('assessments:index')
    else:
        form = AssessmentForm(school=school)
    return render(request, 'assessments/form.html', {'form': form, 'title': 'Nouvelle évaluation'})
