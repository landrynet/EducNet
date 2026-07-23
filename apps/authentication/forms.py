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
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        }),
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
    temporary_password = forms.CharField(
        label='Mot de passe temporaire',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Saisissez le mot de passe reçu',
            'autocomplete': 'current-password',
        }),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = args[0] if args else kwargs.get('user')
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password1'].widget.attrs['placeholder'] = '••••••••'
        self.fields['new_password2'].label = 'Confirmer le mot de passe'
        self.fields['new_password2'].widget.attrs['placeholder'] = '••••••••'
        self.fields['new_password1'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['new_password2'].widget.attrs['autocomplete'] = 'new-password'
        self.order_fields(['temporary_password', 'new_password1', 'new_password2'])
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('temporary_password', css_class='form-control'),
            Field('new_password1', css_class='form-control'),
            Field('new_password2', css_class='form-control'),
            Submit('submit', 'Changer le mot de passe', css_class='btn btn-primary w-100 mt-3'),
        )

    def clean_temporary_password(self):
        temporary_password = self.cleaned_data.get('temporary_password')
        if not temporary_password:
            raise forms.ValidationError(
                "Saisissez le mot de passe temporaire reçu lors de la création de votre compte."
            )
        if not self.user or not self.user.check_password(temporary_password):
            raise forms.ValidationError("Le mot de passe temporaire est incorrect ou a déjà été invalidé.")
        return temporary_password
