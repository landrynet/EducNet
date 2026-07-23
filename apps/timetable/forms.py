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

    def __init__(self, *args, school=None, **kwargs):
        self.school = school
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and end <= start:
            raise forms.ValidationError("L'heure de fin doit être après l'heure de début.")
        if start and end and self.school:
            overlap = TimeSlot.objects.filter(
                school=self.school,
                start_time__lt=end,
                end_time__gt=start,
            ).exclude(pk=self.instance.pk)
            if overlap.exists():
                raise forms.ValidationError(
                    "Ce créneau chevauche déjà un créneau configuré pour votre école."
                )
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
        self.school = school
        self.classroom = classroom
        super().__init__(*args, **kwargs)
        from apps.academic.models import Subject
        from apps.staff.models import StaffProfile
        from apps.users.models import User, Role

        # Subjects linked to this classroom
        if classroom:
            subjects = classroom.subjects.filter(school=school)
        else:
            subjects = Subject.objects.filter(school=school)
        self.fields['subject'].choices = [('', '— Choisir une matière —')] + [
            (s.pk, s.name) for s in subjects
        ]

        # Only teachers assigned to the selected subject may be submitted.
        # Rebuild this queryset from the submitted subject as well as the
        # initial value so tampered requests cannot broaden the choices.
        subject_id = self.data.get('subject') if self.is_bound else self.initial.get('subject')
        subject = subjects.filter(pk=subject_id).first() if subject_id else None
        teacher_pks = (
            StaffProfile.objects.filter(
                school=school,
                staff_type='teacher',
                is_active=True,
                user__school=school,
                user__role=Role.ENSEIGNANT,
                user__is_active=True,
                subjects=subject,
            ).values_list('user_id', flat=True)
            if subject else []
        )
        teachers = User.objects.filter(pk__in=teacher_pks).order_by('last_name', 'first_name')
        self.fields['teacher'].choices = [('', '— Aucun enseignant —')] + [
            (t.pk, t.get_full_name()) for t in teachers
        ]

    def clean(self):
        cleaned_data = super().clean()
        subject_id = cleaned_data.get('subject')
        teacher_id = cleaned_data.get('teacher')
        if subject_id and teacher_id:
            from apps.academic.models import Subject
            from apps.staff.models import StaffProfile
            from apps.users.models import User, Role

            subject = Subject.objects.filter(
                pk=subject_id,
                school=self.school,
            ).first()
            teacher = User.objects.filter(
                pk=teacher_id, school=self.school, role=Role.ENSEIGNANT,
                is_active=True,
            ).first()
            if not subject or not teacher or not StaffProfile.objects.filter(
                user=teacher, school=self.school, staff_type='teacher',
                is_active=True, subjects=subject,
            ).exists():
                raise forms.ValidationError(
                    "L'enseignant sélectionné n'est pas affecté à cette matière."
                )
        return cleaned_data
