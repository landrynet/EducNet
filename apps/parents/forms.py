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
