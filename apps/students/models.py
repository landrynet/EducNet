"""Student models — V1.4: per-school unique matricule + configurable auto-generation."""

from django.db import models, transaction
from django.utils import timezone


class Gender(models.TextChoices):
    MALE = 'M', 'Masculin'
    FEMALE = 'F', 'Féminin'


class MatriculeConfig(models.Model):
    """Per-school matricule format configuration.

    Each school owns exactly one config record (created on demand).
    The sequence counter (last_sequence) is incremented atomically so
    two concurrent saves never produce the same matricule.

    Format: [prefix<sep>][year<sep>]<zero-padded-seq>
    Examples with defaults: 2026-0001, 2026-0002 …
    With prefix='ELV': ELV-2026-0001
    With include_year=False: 0001, 0002 …
    """

    school = models.OneToOneField(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='matricule_config',
        verbose_name='École',
    )
    prefix = models.CharField(
        max_length=10, blank=True, default='',
        verbose_name='Préfixe (ex. ELV, 22)',
        help_text='Laissez vide pour ne pas utiliser de préfixe.',
    )
    include_year = models.BooleanField(
        default=True,
        verbose_name='Inclure l\'année en cours',
    )
    include_initials = models.BooleanField(
        default=False,
        verbose_name='Inclure les initiales de l\'élève',
        help_text='Ajoute la 1ère lettre du prénom et du nom (ex. KJ pour Konan Jean).',
    )
    separator = models.CharField(
        max_length=3, default='-',
        verbose_name='Séparateur',
    )
    num_digits = models.PositiveSmallIntegerField(
        default=4,
        verbose_name='Nombre de chiffres du numéro séquentiel',
        help_text='Ex. 4 → 0001, 0002 …',
    )
    last_sequence = models.PositiveIntegerField(
        default=0,
        verbose_name='Dernier numéro de séquence',
    )

    class Meta:
        verbose_name = 'Configuration matricule'
        verbose_name_plural = 'Configurations matricule'

    def __str__(self):
        return f"Config matricule — {self.school}"

    def _build_parts(self, sequence, first_name='', last_name=''):
        """Assemble matricule components in order: prefix, initials, year, sequence."""
        parts = []
        if self.prefix:
            parts.append(self.prefix)
        if self.include_initials:
            fn = (first_name or '').strip()
            ln = (last_name or '').strip()
            initials = f"{fn[:1]}{ln[:1]}".upper() if fn or ln else 'XX'
            parts.append(initials)
        if self.include_year:
            parts.append(str(timezone.now().year))
        parts.append(str(sequence).zfill(self.num_digits))
        return self.separator.join(parts)

    def preview(self, first_name='', last_name=''):
        """Return a preview of the next matricule without incrementing the counter."""
        return self._build_parts(self.last_sequence + 1, first_name, last_name)

    def generate_next(self, first_name='', last_name=''):
        """Atomically increment the sequence and return the new matricule string."""
        with transaction.atomic():
            # Re-fetch with a row-level lock to prevent duplicates under concurrency.
            config = MatriculeConfig.objects.select_for_update().get(pk=self.pk)
            config.last_sequence += 1
            config.save(update_fields=['last_sequence'])
            self.last_sequence = config.last_sequence
        return self._build_parts(self.last_sequence, first_name, last_name)


class Student(models.Model):
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE, related_name='students',
    )
    # Identity
    # V1.4: unique constraint is now per-school, not global.
    student_id = models.CharField(max_length=30, verbose_name='Matricule', blank=True)
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
        # V1.4: matricule must be unique within each school, not globally.
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'student_id'],
                name='unique_student_id_per_school',
            )
        ]

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

    # ── V1.4: auto-generate matricule on first save ────────────────────────

    def save(self, *args, **kwargs):
        if not self.student_id and self.school_id:
            config, _ = MatriculeConfig.objects.get_or_create(school_id=self.school_id)
            self.student_id = config.generate_next(
                first_name=self.first_name,
                last_name=self.last_name,
            )
        super().save(*args, **kwargs)
