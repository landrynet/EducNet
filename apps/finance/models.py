"""Finance models: fees, payments, expenses."""

from django.db import models
from django.utils import timezone


class FeeType(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='fee_types')
    name = models.CharField(max_length=100, verbose_name='Type de frais')
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Montant')
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE, null=True, blank=True)
    level = models.ForeignKey('academic.Level', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Niveau')

    class Meta:
        verbose_name = 'Type de frais'
        verbose_name_plural = 'Types de frais'

    def __str__(self):
        return f"{self.name} — {self.amount} FCFA"


class Payment(models.Model):
    STATUS = [
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('partial', 'Partiel'),
        ('overdue', 'En retard'),
        ('cancelled', 'Annulé'),
    ]
    METHODS = [
        ('cash', 'Espèces'),
        ('mobile_money', 'Mobile Money'),
        ('bank', 'Virement bancaire'),
        ('check', 'Chèque'),
    ]
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='payments')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='payments')
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Montant dû')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Montant payé')
    payment_date = models.DateField(default=timezone.now, verbose_name='Date de paiement')
    method = models.CharField(max_length=20, choices=METHODS, default='cash', verbose_name='Mode de paiement')
    reference = models.CharField(max_length=100, blank=True, verbose_name='Référence')
    status = models.CharField(max_length=20, choices=STATUS, default='paid')
    received_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.student} — {self.fee_type} — {self.amount} FCFA"
