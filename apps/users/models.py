"""Custom User model with multi-tenant role-based access."""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class Role(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'Super Administrateur'
    ADMIN_ECOLE = 'admin_ecole', "Administrateur d'École"
    SECRETAIRE = 'secretaire', 'Secrétaire'
    ENSEIGNANT = 'enseignant', 'Enseignant'
    COMPTABLE = 'comptable', 'Comptable'


class UserManager(BaseUserManager):
    """Custom manager for the User model using email as username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', Role.SUPER_ADMIN)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('must_change_password', False)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for the school management system.
    All users except Super Admin belong to a specific school (multi-tenant).
    """
    email = models.EmailField(unique=True, verbose_name='Adresse email')
    first_name = models.CharField(max_length=100, verbose_name='Prénom')
    last_name = models.CharField(max_length=100, verbose_name='Nom')
    role = models.CharField(max_length=20, choices=Role.choices, verbose_name='Rôle')
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='École',
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    photo = models.ImageField(upload_to='users/photos/', blank=True, null=True, verbose_name='Photo')
    address = models.TextField(blank=True, verbose_name='Adresse')

    # Account state
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    is_staff = models.BooleanField(default=False, verbose_name='Staff')
    must_change_password = models.BooleanField(default=True, verbose_name='Doit changer le mot de passe')
    profile_completed = models.BooleanField(default=False, verbose_name='Profil complété')

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Date d\'inscription')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='Dernière IP')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    objects = UserManager()

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_super_admin(self):
        return self.role == Role.SUPER_ADMIN

    @property
    def is_admin_ecole(self):
        return self.role == Role.ADMIN_ECOLE

    @property
    def is_secretaire(self):
        return self.role == Role.SECRETAIRE

    @property
    def is_enseignant(self):
        return self.role == Role.ENSEIGNANT

    @property
    def is_comptable(self):
        return self.role == Role.COMPTABLE

    @property
    def initials(self):
        parts = [self.first_name[:1], self.last_name[:1]]
        return ''.join(p for p in parts if p).upper()
