"""Document and archive models."""

from django.db import models
from django.utils import timezone


class DocumentCategory(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='document_categories')
    name = models.CharField(max_length=100, verbose_name='Catégorie')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Catégorie de document'

    def __str__(self):
        return self.name


class Document(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='documents')
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200, verbose_name='Titre')
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/%Y/%m/', verbose_name='Fichier')
    uploaded_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='documents')
    student = models.ForeignKey('students.Student', on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    uploaded_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title
