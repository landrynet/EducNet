"""Timetable models."""

from django.db import models


DAYS = [
    (0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'),
    (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi'),
]


class TimeSlot(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='timeslots')
    name = models.CharField(max_length=50, verbose_name='Nom (ex: 8h-9h)')
    start_time = models.TimeField(verbose_name='Heure de début')
    end_time = models.TimeField(verbose_name='Heure de fin')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'start_time']

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')}"


class TimetableEntry(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='timetable_entries')
    classroom = models.ForeignKey('academic.Classroom', on_delete=models.CASCADE, related_name='timetable_entries')
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE)
    teacher = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    day = models.PositiveSmallIntegerField(choices=DAYS, verbose_name='Jour')
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    room = models.CharField(max_length=50, blank=True, verbose_name='Salle')

    class Meta:
        verbose_name = 'Entrée emploi du temps'
        unique_together = ('classroom', 'day', 'timeslot')

    def __str__(self):
        return f"{self.classroom} — {self.subject} ({self.get_day_display()})"
