"""Forms for the timetable module."""

from django import forms
from .models import TimeSlot, TimetableEntry


class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['start_time', 'end_time', 'slot_type', 'name', 'order']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'slot_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Cours 1 (optionnel)'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'start_time': 'Heure de début',
            'end_time': 'Heure de fin',
            'slot_type': 'Type',
            'name': 'Nom (optionnel)',
            'order': 'Ordre',
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and end <= start:
            raise forms.ValidationError("L'heure de fin doit être après l'heure de début.")
        return cleaned_data


class TimetableEntryForm(forms.Form):
    """Dynamic form for adding/editing a course in the timetable."""
    subject = forms.ChoiceField(
        label='Matière',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    teacher = forms.ChoiceField(
        label='Enseignant',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    room = forms.CharField(
        label='Salle',
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Salle 3 (optionnel)'})
    )

    def __init__(self, *args, school=None, classroom=None, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.academic.models import Subject
        from apps.users.models import User, Role

        # Subjects linked to this classroom
        if classroom:
            subjects = classroom.subjects.filter(school=school)
        else:
            subjects = Subject.objects.filter(school=school)
        self.fields['subject'].choices = [('', '— Choisir une matière —')] + [
            (s.pk, s.name) for s in subjects
        ]

        # Teachers of this school
        teachers = User.objects.filter(school=school, role=Role.ENSEIGNANT, is_active=True)
        self.fields['teacher'].choices = [('', '— Aucun enseignant —')] + [
            (t.pk, t.get_full_name()) for t in teachers
        ]
