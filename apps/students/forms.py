from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset
from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'student_id', 'first_name', 'last_name', 'gender',
            'date_of_birth', 'place_of_birth', 'nationality',
            'address', 'phone', 'email', 'photo',
            'previous_school', 'medical_notes',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'medical_notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Identité',
                Row(Column('first_name'), Column('last_name')),
                Row(Column('student_id'), Column('gender')),
                Row(Column('date_of_birth'), Column('place_of_birth')),
                Row(Column('nationality')),
                'photo',
            ),
            Fieldset('Coordonnées',
                'address',
                Row(Column('phone'), Column('email')),
            ),
            Fieldset('Informations scolaires',
                'previous_school',
                'medical_notes',
            ),
            Submit('submit', 'Enregistrer', css_class='btn btn-primary mt-3'),
        )
