from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Parent


class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = ['first_name', 'last_name', 'relationship', 'phone', 'phone2', 'email', 'address', 'profession', 'children']
        widgets = {'address': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            from apps.students.models import Student
            self.fields['children'].queryset = Student.objects.filter(school=school, is_active=True)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name'), Column('last_name')),
            Row(Column('relationship'), Column('profession')),
            Row(Column('phone'), Column('phone2')),
            'email', 'address', 'children',
            Submit('submit', 'Enregistrer', css_class='btn btn-primary'),
        )

    def clean_children(self):
        children = self.cleaned_data.get('children')
        if not children:
            return children
        school_ids = {child.school_id for child in children}
        if len(school_ids) > 1:
            raise forms.ValidationError(
                "Les élèves associés doivent appartenir au même établissement."
            )
        if self.instance.pk and self.instance.school_id not in school_ids:
            raise forms.ValidationError(
                "Un parent ne peut être associé qu'aux élèves de son établissement."
            )
        for child in children:
            existing = child.parents.filter(is_active=True).exclude(pk=self.instance.pk if self.instance.pk else None)
            if existing.exists():
                names = ', '.join(parent.get_full_name() for parent in existing[:2])
                raise forms.ValidationError(
                    f"{child.get_full_name()} est déjà associé à un tuteur principal ({names}). "
                    "Modifiez d'abord l'association existante."
                )
        return children
