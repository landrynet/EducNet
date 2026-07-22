"""Transport models."""

from django.db import models


class Route(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='routes')
    name = models.CharField(max_length=100, verbose_name='Nom du circuit')
    description = models.TextField(blank=True)
    driver_name = models.CharField(max_length=100, blank=True, verbose_name='Nom du chauffeur')
    driver_phone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone chauffeur')
    vehicle_number = models.CharField(max_length=20, blank=True, verbose_name='Numéro véhicule')
    capacity = models.PositiveIntegerField(default=30, verbose_name='Capacité')
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Tarif mensuel')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Circuit'
        verbose_name_plural = 'Circuits'

    def __str__(self):
        return self.name


class StudentTransport(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='student_transports')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='transport')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='students')
    pickup_point = models.CharField(max_length=200, blank=True, verbose_name='Point de prise en charge')
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'academic_year')
        verbose_name = 'Transport élève'
