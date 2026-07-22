"""Report card models."""

from django.db import models


class ReportCard(models.Model):
    STATUS = [
        ('draft', 'Brouillon'),
        ('validated', 'Validé'),
        ('published', 'Publié'),
    ]
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='report_cards')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='report_cards')
    enrollment = models.ForeignKey('enrollment.Enrollment', on_delete=models.CASCADE, related_name='report_cards')
    period = models.ForeignKey('academic.Period', on_delete=models.CASCADE)
    average = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Moyenne générale')
    rank = models.PositiveIntegerField(null=True, blank=True, verbose_name='Rang')
    class_average = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Moyenne de classe')
    teacher_comment = models.TextField(blank=True, verbose_name='Appréciation du professeur principal')
    director_comment = models.TextField(blank=True, verbose_name='Appréciation du directeur')
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'period')
        verbose_name = 'Bulletin'
        verbose_name_plural = 'Bulletins'
        ordering = ['-period__order']

    def __str__(self):
        return f"Bulletin {self.student} — {self.period}"
