"""Communication models: announcements, messages."""

from django.db import models
from django.utils import timezone


class Announcement(models.Model):
    PRIORITY = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('urgent', 'Urgente'),
    ]
    TARGET_AUDIENCE = [
        ('all', 'Tout le monde'),
        ('teachers', 'Enseignants'),
        ('students', 'Élèves'),
        ('parents', 'Parents'),
        ('staff', 'Personnel'),
    ]
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='announcements')
    author = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200, verbose_name='Titre')
    content = models.TextField(verbose_name='Contenu')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE, default='all')
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Annonce'
        verbose_name_plural = 'Annonces'
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class Message(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='sent_messages')
    recipients = models.ManyToManyField('users.User', related_name='received_messages', blank=True)
    subject = models.CharField(max_length=200, verbose_name='Objet')
    body = models.TextField(verbose_name='Message')
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.subject} — {self.sender}"
