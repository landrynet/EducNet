from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={'placeholder': 'votre@email.com', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('username', css_class='form-control form-control-lg'),
            Field('password', css_class='form-control form-control-lg'),
            Submit('submit', 'Se connecter', css_class='btn btn-primary btn-lg w-100 mt-3'),
        )
        self.helper.form_class = 'needs-validation'


class ChangePasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password1'].widget.attrs['placeholder'] = '••••••••'
        self.fields['new_password2'].label = 'Confirmer le mot de passe'
        self.fields['new_password2'].widget.attrs['placeholder'] = '••••••••'
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('new_password1', css_class='form-control'),
            Field('new_password2', css_class='form-control'),
            Submit('submit', 'Changer le mot de passe', css_class='btn btn-primary w-100 mt-3'),
        )
