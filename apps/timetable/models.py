"""Timetable models."""

from django.db import models
from django.utils import timezone


DAYS = [
    (0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'),
    (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi'),
]

SLOT_TYPE_CHOICES = [
    ('course', 'Cours'),
    ('break', 'Pause'),
]

STATUS_CHOICES = [
    ('draft', 'Brouillon'),
    ('preparing', 'En préparation'),
    ('published', 'Publié'),
]


class TimeSlot(models.Model):
    """A time period in the school day (course slot or break)."""
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE, related_name='timeslots'
    )
    name = models.CharField(max_length=80, verbose_name='Nom', blank=True)
    start_time = models.TimeField(verbose_name='Heure de début')
    end_time = models.TimeField(verbose_name='Heure de fin')
    slot_type = models.CharField(
        max_length=10, choices=SLOT_TYPE_CHOICES, default='course',
        verbose_name='Type'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Ordre')

    class Meta:
        ordering = ['order', 'start_time']
        verbose_name = 'Créneau horaire'
        verbose_name_plural = 'Créneaux horaires'

    def __str__(self):
        label = self.name or f"{self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')}"
        return label

    @property
    def time_range(self):
        return f"{self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')}"

    @property
    def is_break(self):
        return self.slot_type == 'break'

    @property
    def duration_minutes(self):
        """Duration in minutes."""
        start = self.start_time.hour * 60 + self.start_time.minute
        end = self.end_time.hour * 60 + self.end_time.minute
        return end - start


class TimetableSchedule(models.Model):
    """Tracks the publication status of a classroom's timetable."""
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE, related_name='timetable_schedules'
    )
    classroom = models.OneToOneField(
        'academic.Classroom', on_delete=models.CASCADE, related_name='timetable_schedule'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft',
        verbose_name='Statut'
    )
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de publication')
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_schedules'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Planning emploi du temps'
        verbose_name_plural = 'Plannings emplois du temps'

    def __str__(self):
        return f"{self.classroom} — {self.get_status_display()}"

    def publish(self, user=None):
        self.status = 'published'
        self.published_at = timezone.now()
        if user:
            self.created_by = user
        self.save()

    @property
    def is_published(self):
        return self.status == 'published'

    @property
    def status_badge_class(self):
        return {
            'draft': 'secondary',
            'preparing': 'warning',
            'published': 'success',
        }.get(self.status, 'secondary')


class SchoolConfig(models.Model):
    """Per-school timetable configuration (working days)."""
    school = models.OneToOneField(
        'schools.School', on_delete=models.CASCADE, related_name='timetable_config'
    )
    # List of day indices that are working days, e.g. [0,1,2,3,4] = Mon–Fri
    working_days = models.JSONField(
        default=list, verbose_name='Jours de cours',
        help_text='Indices des jours travaillés (0=Lundi, 5=Samedi)'
    )

    class Meta:
        verbose_name = 'Configuration emploi du temps'

    def __str__(self):
        return f"Config {self.school}"

    def get_working_days(self):
        """Return list of (day_index, day_label) for working days."""
        days = self.working_days or [0, 1, 2, 3, 4]
        return [(i, label) for i, label in DAYS if i in days]

    def save(self, *args, **kwargs):
        # Ensure default
        if not self.working_days:
            self.working_days = [0, 1, 2, 3, 4]
        super().save(*args, **kwargs)


class TimetableEntry(models.Model):
    """A single course slot in the timetable."""
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE, related_name='timetable_entries'
    )
    classroom = models.ForeignKey(
        'academic.Classroom', on_delete=models.CASCADE, related_name='timetable_entries'
    )
    subject = models.ForeignKey(
        'academic.Subject', on_delete=models.CASCADE, related_name='timetable_entries'
    )
    teacher = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='timetable_entries', verbose_name='Enseignant'
    )
    day = models.PositiveSmallIntegerField(choices=DAYS, verbose_name='Jour')
    timeslot = models.ForeignKey(
        TimeSlot, on_delete=models.CASCADE, related_name='entries'
    )
    room = models.CharField(max_length=50, blank=True, verbose_name='Salle')

    class Meta:
        verbose_name = 'Cours'
        verbose_name_plural = 'Cours'
        unique_together = ('classroom', 'day', 'timeslot')

    def __str__(self):
        return f"{self.classroom} — {self.subject} ({self.get_day_display()})"
