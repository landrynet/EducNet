"""Academic organization models: years, levels, classes, subjects."""

from django.db import models


class AcademicYear(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='academic_years')
    name = models.CharField(max_length=20, verbose_name='Nom (ex: 2024-2025)')
    start_date = models.DateField(verbose_name='Date de début')
    end_date = models.DateField(verbose_name='Date de fin')
    is_current = models.BooleanField(default=False, verbose_name='Année en cours')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Année scolaire'
        verbose_name_plural = 'Années scolaires'
        unique_together = ('school', 'name')
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} — {self.school.name}"

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.filter(school=self.school, is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


class Level(models.Model):
    """Academic level (e.g., 6ème, 5ème, Terminale, CE1, etc.)."""
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='levels')
    name = models.CharField(max_length=50, verbose_name='Nom du niveau')
    order = models.PositiveIntegerField(default=0, verbose_name='Ordre d\'affichage')

    class Meta:
        verbose_name = 'Niveau'
        verbose_name_plural = 'Niveaux'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Classroom(models.Model):
    """A class/group within a level for a specific academic year."""
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='classrooms')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='classrooms')
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='classrooms')
    name = models.CharField(max_length=50, verbose_name='Nom de la classe (ex: 3ème A)')
    capacity = models.PositiveIntegerField(default=40, verbose_name='Capacité')
    class_teacher = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='managed_classes',
        verbose_name='Professeur principal'
    )

    class Meta:
        verbose_name = 'Classe'
        verbose_name_plural = 'Classes'
        ordering = ['level__order', 'name']

    def __str__(self):
        return f"{self.name} ({self.academic_year.name})"

    @property
    def student_count(self):
        return self.enrollments.filter(status='active').count()


class Subject(models.Model):
    """A subject/discipline taught in the school."""
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100, verbose_name='Matière')
    code = models.CharField(max_length=10, blank=True, verbose_name='Code')
    coefficient = models.DecimalField(max_digits=4, decimal_places=2, default=1, verbose_name='Coefficient')
    color = models.CharField(max_length=7, default='#4e73df', verbose_name='Couleur (hex)')

    class Meta:
        verbose_name = 'Matière'
        verbose_name_plural = 'Matières'
        ordering = ['name']

    def __str__(self):
        return self.name


class Period(models.Model):
    """Marking period (trimester, semester, etc.)."""
    PERIOD_TYPES = [
        ('trimester', 'Trimestre'),
        ('semester', 'Semestre'),
        ('term', 'Terme'),
    ]
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='periods')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='periods')
    name = models.CharField(max_length=50, verbose_name='Nom (ex: 1er Trimestre)')
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, default='trimester')
    start_date = models.DateField()
    end_date = models.DateField()
    order = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Période'
        verbose_name_plural = 'Périodes'
        ordering = ['order']

    def __str__(self):
        return f"{self.name} — {self.academic_year.name}"
