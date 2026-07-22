from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import AcademicYear, Level, Classroom, Subject, Period


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_current']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enregistrer', css_class='btn btn-primary'))


class LevelForm(forms.ModelForm):
    class Meta:
        model = Level
        fields = ['name', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enregistrer', css_class='btn btn-primary'))


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['academic_year', 'level', 'name', 'capacity', 'class_teacher']

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(school=school)
            self.fields['level'].queryset = Level.objects.filter(school=school)
            from apps.users.models import User
            self.fields['class_teacher'].queryset = User.objects.filter(
                school=school, role='enseignant', is_active=True
            )
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('academic_year'), Column('level')),
            Row(Column('name'), Column('capacity')),
            'class_teacher',
            Submit('submit', 'Enregistrer', css_class='btn btn-primary'),
        )


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'coefficient', 'color']
        widgets = {'color': forms.TextInput(attrs={'type': 'color'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('name'), Column('code')),
            Row(Column('coefficient'), Column('color')),
            Submit('submit', 'Enregistrer', css_class='btn btn-primary'),
        )
