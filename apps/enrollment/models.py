"""Enrollment models — links students to classrooms per academic year."""

from django.db import models
from django.utils import timezone


class Enrollment(models.Model):
    STATUS = [
        ('pending', 'En attente'),
        ('active', 'Actif'),
        ('transferred', 'Transféré'),
        ('withdrawn', 'Retiré'),
        ('graduated', 'Diplômé'),
    ]
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='enrollments')
    classroom = models.ForeignKey('academic.Classroom', on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS, default='active', verbose_name='Statut')
    enrollment_date = models.DateField(default=timezone.now, verbose_name='Date d\'inscription')
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'
        unique_together = ('student', 'academic_year')
        ordering = ['-enrollment_date']

    def __str__(self):
        return f"{self.student} → {self.classroom} ({self.academic_year.name})"
