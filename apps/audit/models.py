"""Audit log models — records all important user actions."""

from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class AuditAction(models.TextChoices):
    LOGIN = 'LOGIN', 'Connexion'
    LOGOUT = 'LOGOUT', 'Déconnexion'
    CREATE = 'CREATE', 'Création'
    UPDATE = 'UPDATE', 'Modification'
    DELETE = 'DELETE', 'Suppression'
    VIEW = 'VIEW', 'Consultation'
    EXPORT = 'EXPORT', 'Export'
    OTHER = 'OTHER', 'Autre'


class AuditLog(models.Model):
    user = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_logs',
        verbose_name='Utilisateur'
    )
    school = models.ForeignKey(
        'schools.School', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_logs',
        verbose_name='École'
    )
    action = models.CharField(max_length=20, choices=AuditAction.choices, verbose_name='Action')
    description = models.TextField(verbose_name='Description')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Adresse IP')
    user_agent = models.CharField(max_length=300, blank=True, verbose_name='Navigateur')

    # Generic FK to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    timestamp = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='Horodatage')

    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journaux d'audit"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['school', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.get_action_display()} — {self.user} — {self.description[:60]}"
