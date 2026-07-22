"""School model — the core multi-tenant entity."""

from django.db import models
from django.utils import timezone


class SchoolType(models.TextChoices):
    PRIMAIRE = 'primaire', 'École Primaire'
    SECONDAIRE = 'secondaire', 'École Secondaire'
    LYCEE = 'lycee', 'Lycée'
    UNIVERSITE = 'universite', 'Université'
    AUTRE = 'autre', 'Autre'


class School(models.Model):
    """Represents an educational institution in the multi-tenant system."""
    name = models.CharField(max_length=200, verbose_name='Nom de l\'établissement')
    code = models.CharField(max_length=20, unique=True, verbose_name='Code')
    school_type = models.CharField(
        max_length=20, choices=SchoolType.choices,
        default=SchoolType.SECONDAIRE, verbose_name='Type d\'établissement'
    )
    address = models.TextField(verbose_name='Adresse')
    city = models.CharField(max_length=100, verbose_name='Ville')
    country = models.CharField(max_length=100, default='Côte d\'Ivoire', verbose_name='Pays')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')
    website = models.URLField(blank=True, verbose_name='Site web')
    logo = models.ImageField(upload_to='schools/logos/', blank=True, null=True, verbose_name='Logo')
    director_name = models.CharField(max_length=200, blank=True, verbose_name='Nom du directeur')
    registration_number = models.CharField(max_length=50, blank=True, verbose_name='Numéro d\'agrément')
    founded_year = models.PositiveIntegerField(null=True, blank=True, verbose_name='Année de fondation')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Date de création')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Dernière modification')

    class Meta:
        verbose_name = 'École'
        verbose_name_plural = 'Écoles'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def user_count(self):
        return self.users.filter(is_active=True).count()

    @property
    def student_count(self):
        return self.students.filter(is_active=True).count() if hasattr(self, 'students') else 0
