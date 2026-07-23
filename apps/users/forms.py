"""Forms for user management."""

from django import forms
from django.contrib.auth.forms import SetPasswordForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import User, Role


class UserCreateForm(forms.ModelForm):
    """Form to create a new user by Admin École."""
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Mot de passe temporaire',
        min_length=8,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirmer le mot de passe',
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'phone', 'address', 'photo']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, school=None, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        # Super admin can assign any role; Admin école cannot create super admin
        if current_user and not current_user.is_super_admin:
            self.fields['role'].choices = [
                c for c in Role.choices if c[0] != Role.SUPER_ADMIN
            ]
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name'), Column('last_name')),
            'email',
            Row(Column('role'), Column('phone')),
            'address',
            'photo',
            Row(Column('password'), Column('confirm_password')),
            Submit('submit', 'Créer l\'utilisateur', css_class='btn btn-primary'),
        )

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if pwd and confirm and pwd != confirm:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.must_change_password = True
        if self.school:
            user.school = self.school
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    """Form to edit an existing user."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'address', 'photo', 'is_active']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name'), Column('last_name')),
            Row(Column('phone'), Column('is_active')),
            'address',
            'photo',
            Submit('submit', 'Enregistrer', css_class='btn btn-primary'),
        )


class ProfileForm(forms.ModelForm):
    """Form for users to update their own profile."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'address', 'photo']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prénom et Nom sont obligatoires pour l'assistant de configuration
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Mettre à jour le profil', css_class='btn btn-primary'))
