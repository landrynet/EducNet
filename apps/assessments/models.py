"""Assessment and grade models."""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class AssessmentType(models.TextChoices):
    EXAM = 'exam', 'Examen'
    QUIZ = 'quiz', 'Interrogation'
    HOMEWORK = 'homework', 'Devoir maison'
    ORAL = 'oral', 'Oral'
    PROJECT = 'project', 'Projet'


class Assessment(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='assessments')
    classroom = models.ForeignKey('academic.Classroom', on_delete=models.CASCADE, related_name='assessments')
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE)
    period = models.ForeignKey('academic.Period', on_delete=models.CASCADE, null=True, blank=True)
    teacher = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    assessment_type = models.CharField(max_length=20, choices=AssessmentType.choices, default=AssessmentType.EXAM)
    title = models.CharField(max_length=200, verbose_name='Titre')
    date = models.DateField(verbose_name='Date')
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=20, verbose_name='Note maximale')
    coefficient = models.DecimalField(max_digits=4, decimal_places=2, default=1, verbose_name='Coefficient')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Évaluation'
        verbose_name_plural = 'Évaluations'
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} — {self.classroom} ({self.subject})"


class Grade(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='grades')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='grades')
    score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Note'
    )
    is_absent = models.BooleanField(default=False, verbose_name='Absent')
    comment = models.CharField(max_length=200, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('assessment', 'student')
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'

    def __str__(self):
        return f"{self.student} — {self.assessment}: {self.score}"
