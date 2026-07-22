"""Parent/guardian models."""

from django.db import models


class Parent(models.Model):
    RELATIONSHIP = [
        ('pere', 'Père'),
        ('mere', 'Mère'),
        ('tuteur', 'Tuteur légal'),
        ('autre', 'Autre'),
    ]
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='parents')
    first_name = models.CharField(max_length=100, verbose_name='Prénom')
    last_name = models.CharField(max_length=100, verbose_name='Nom')
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP, default='pere', verbose_name='Lien')
    phone = models.CharField(max_length=20, verbose_name='Téléphone')
    phone2 = models.CharField(max_length=20, blank=True, verbose_name='Téléphone 2')
    email = models.EmailField(blank=True, verbose_name='Email')
    address = models.TextField(blank=True, verbose_name='Adresse')
    profession = models.CharField(max_length=100, blank=True, verbose_name='Profession')
    children = models.ManyToManyField('students.Student', related_name='parents', blank=True, verbose_name='Enfants')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Parent / Tuteur'
        verbose_name_plural = 'Parents & Tuteurs'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_relationship_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
