"""School forms — V1.4: school code is now auto-generated, removed from all forms."""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset
from .models import School


class SchoolForm(forms.ModelForm):
    """Edit an existing school (super admin). The code is technical and never editable."""

    class Meta:
        model = School
        fields = [
            'name', 'school_type', 'address', 'city', 'country',
            'phone', 'email', 'website', 'logo', 'director_name',
            'registration_number', 'founded_year', 'is_active',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ('name', 'address', 'city', 'country'):
            self.fields[field].required = True
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Informations générales',
                Row(Column('name', css_class='col-md-8'), Column('school_type', css_class='col-md-4')),
                Row(Column('founded_year'), Column('director_name')),
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


class SchoolSettingsForm(SchoolForm):
    """Settings form for school admins — school_type is shown read-only, not editable."""

    class Meta(SchoolForm.Meta):
        # Exclude school_type from editable fields; it is displayed separately in the template.
        fields = [
            'name', 'address', 'city', 'country',
            'phone', 'email', 'website', 'logo', 'director_name',
            'registration_number', 'founded_year',
        ]

    def __init__(self, *args, **kwargs):
        super(SchoolForm, self).__init__(*args, **kwargs)  # skip SchoolForm.__init__ helper setup
        for field in ('name', 'address', 'city', 'country'):
            self.fields[field].required = True
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Informations générales',
                'name',
                Row(Column('founded_year'), Column('director_name')),
                'registration_number',
            ),
            Fieldset('Coordonnées',
                'address',
                Row(Column('city'), Column('country')),
                Row(Column('phone'), Column('email')),
                'website',
            ),
            Fieldset('Médias',
                'logo',
            ),
            Submit('submit', 'Enregistrer les modifications', css_class='btn btn-primary mt-3'),
        )


class SchoolCreationForm(forms.ModelForm):
    """Initial school creation by Super Admin.

    V1.4: The school code is auto-generated server-side — the Super Admin
    does not enter it manually.
    """

    class Meta:
        model = School
        fields = [
            'name', 'school_type', 'address', 'city', 'country',
            'phone', 'email', 'website', 'logo', 'registration_number',
            'founded_year',
        ]
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Informations initiales',
                Row(Column('name', css_class='col-md-8'), Column('school_type', css_class='col-md-4')),
                Row(Column('founded_year'), Column('director_name') if 'director_name' in self.fields else Column()),
                'registration_number',
            ),
            Fieldset('Coordonnées',
                'address',
                Row(Column('city'), Column('country')),
                Row(Column('phone'), Column('email')),
                'website',
            ),
            Fieldset('Logo', 'logo'),
            Submit('submit', 'Créer l\'école', css_class='btn btn-primary mt-3'),
        )
