from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from apps.authentication.decorators import role_required
from .models import Assessment, AssessmentType, Grade
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
    search = request.GET.get('q', '').strip()
    assessment_type = request.GET.get('type', '').strip()
    if search:
        assessments = assessments.filter(
            Q(title__icontains=search)
            | Q(classroom__name__icontains=search)
            | Q(subject__name__icontains=search)
        )
    if assessment_type:
        assessments = assessments.filter(assessment_type=assessment_type)
    paginator = Paginator(assessments, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'assessments/index.html', {
        'page_obj': page,
        'search': search,
        'assessment_type': assessment_type,
        'assessment_types': AssessmentType.choices,
        'title': 'Évaluations',
    })


@login_required
@role_required(['admin_ecole', 'enseignant', 'super_admin'])
def assessment_detail(request, pk):
    school = request.user.school
    assessment = get_object_or_404(
        Assessment.objects.select_related('classroom', 'subject', 'period', 'teacher'),
        pk=pk,
        **({'school': school} if school else {}),
    )
    if request.user.is_enseignant and assessment.teacher_id != request.user.id:
        return redirect('assessments:index')
    return render(request, 'assessments/detail.html', {
        'assessment': assessment,
        'title': 'Détails de l’évaluation',
    })


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
