"""Student models."""

from django.db import models
from django.utils import timezone


class Gender(models.TextChoices):
    MALE = 'M', 'Masculin'
    FEMALE = 'F', 'Féminin'


class Student(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='students')
    # Identity
    student_id = models.CharField(max_length=20, verbose_name='Matricule', unique=True)
    first_name = models.CharField(max_length=100, verbose_name='Prénom')
    last_name = models.CharField(max_length=100, verbose_name='Nom')
    gender = models.CharField(max_length=1, choices=Gender.choices, verbose_name='Genre')
    date_of_birth = models.DateField(verbose_name='Date de naissance')
    place_of_birth = models.CharField(max_length=100, blank=True, verbose_name='Lieu de naissance')
    nationality = models.CharField(max_length=50, default='Ivoirienne', verbose_name='Nationalité')
    photo = models.ImageField(upload_to='students/photos/', blank=True, null=True)

    # Contact
    address = models.TextField(blank=True, verbose_name='Adresse')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')

    # Academic
    previous_school = models.CharField(max_length=200, blank=True, verbose_name='École précédente')
    medical_notes = models.TextField(blank=True, verbose_name='Notes médicales')

    # Status
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    registered_at = models.DateTimeField(default=timezone.now, verbose_name='Date d\'enregistrement')

    class Meta:
        verbose_name = 'Élève'
        verbose_name_plural = 'Élèves'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.student_id})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = timezone.now().date()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    @property
    def initials(self):
        return f"{self.first_name[:1]}{self.last_name[:1]}".upper()
