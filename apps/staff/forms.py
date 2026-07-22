"""Forms for Staff management."""

from django import forms
from .models import StaffProfile
from apps.users.models import User, Role


class StaffUserForm(forms.ModelForm):
    """Form for creating/editing the User part of a staff member."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        required=False,
        label="Mot de passe",
        help_text="Laisser vide pour ne pas modifier. Obligatoire à la création.",
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'role']
        widgets = {
            'role': forms.Select(choices=[
                (Role.ENSEIGNANT, 'Enseignant'),
                (Role.SECRETAIRE, 'Secrétaire'),
                (Role.COMPTABLE, 'Comptable'),
                (Role.ADMIN_ECOLE, "Administrateur d'École"),
            ]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restrict roles to school-level roles only
        self.fields['role'].choices = [
            (Role.ENSEIGNANT, 'Enseignant'),
            (Role.SECRETAIRE, 'Secrétaire'),
            (Role.COMPTABLE, 'Comptable'),
            (Role.ADMIN_ECOLE, "Administrateur d'École"),
        ]
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['role'].widget.attrs['class'] = 'form-select'

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk and not cleaned_data.get('password'):
            raise forms.ValidationError("Le mot de passe est obligatoire pour un nouveau compte.")
        return cleaned_data


class StaffProfileForm(forms.ModelForm):
    """Form for the StaffProfile details."""

    class Meta:
        model = StaffProfile
        fields = ['staff_type', 'contract_type', 'employee_id', 'hire_date', 'specialization', 'bio', 'is_active']
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'staff_type': forms.Select(attrs={'class': 'form-select'}),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
