from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset
from .models import School


class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            'name', 'code', 'school_type', 'address', 'city', 'country',
            'phone', 'email', 'website', 'logo', 'director_name',
            'registration_number', 'founded_year', 'is_active',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Informations générales',
                Row(Column('name', css_class='col-md-8'), Column('code', css_class='col-md-4')),
                Row(Column('school_type'), Column('founded_year')),
                'director_name',
                'registration_number',
            ),
            Fieldset('Coordonnées',
                'address',
                Row(Column('city'), Column('country')),
                Row(Column('phone'), Column('email')),
                'website',
            ),
            Fieldset('Médias & Statut',
                'logo',
                'is_active',
            ),
            Submit('submit', 'Enregistrer', css_class='btn btn-primary mt-3'),
        )
