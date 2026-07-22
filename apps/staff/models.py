"""Staff models — linked to User accounts."""

from django.db import models


class StaffProfile(models.Model):
    """Extended profile for teaching and non-teaching staff."""
    STAFF_TYPES = [
        ('teacher', 'Enseignant'),
        ('admin', 'Administratif'),
        ('support', 'Personnel de soutien'),
    ]
    CONTRACT_TYPES = [
        ('permanent', 'Permanent'),
        ('contract', 'Contractuel'),
        ('part_time', 'Temps partiel'),
    ]

    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='staff_profile')
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='staff')
    staff_type = models.CharField(max_length=20, choices=STAFF_TYPES, default='teacher', verbose_name='Type')
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES, default='permanent', verbose_name='Contrat')
    employee_id = models.CharField(max_length=20, blank=True, verbose_name='Matricule employé')
    hire_date = models.DateField(null=True, blank=True, verbose_name='Date d\'embauche')
    specialization = models.CharField(max_length=200, blank=True, verbose_name='Spécialisation')
    subjects = models.ManyToManyField('academic.Subject', blank=True, verbose_name='Matières enseignées')
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Salaire')
    bio = models.TextField(blank=True, verbose_name='Biographie')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Profil personnel'
        verbose_name_plural = 'Profils personnel'

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.get_staff_type_display()}"
