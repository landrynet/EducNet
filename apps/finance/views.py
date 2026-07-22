from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from apps.authentication.decorators import role_required
from .models import Payment, FeeType
from apps.audit.utils import log_action
from django import forms


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'fee_type', 'amount_due', 'amount', 'method', 'reference', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school = school
        if school:
            from apps.students.models import Student
            self.fields['student'].queryset = Student.objects.filter(school=school, is_active=True)
            self.fields['fee_type'].queryset = FeeType.objects.filter(school=school)

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        fee_type = cleaned_data.get('fee_type')
        if student and fee_type and student.school_id != fee_type.school_id:
            raise forms.ValidationError(
                "L'élève et le type de frais doivent appartenir au même établissement."
            )
        if self.school and student and student.school_id != self.school.id:
            raise forms.ValidationError("Cet élève n'appartient pas à votre établissement.")
        return cleaned_data


@login_required
@role_required(['admin_ecole', 'comptable', 'super_admin'])
def finance_index(request):
    school = request.user.school
    payments = Payment.objects.filter(school=school).select_related('student', 'fee_type') if school else Payment.objects.all()
    search = request.GET.get('q', '').strip()
    if search:
        payments = payments.filter(
            Q(student__first_name__icontains=search)
            | Q(student__last_name__icontains=search)
            | Q(student__student_id__icontains=search)
        )
    stats = {
        'total_collected': payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0,
        'pending_count': payments.filter(status='pending').count(),
        'total_payments': payments.count(),
    }
    paginator = Paginator(payments, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'finance/index.html', {
        'page_obj': page,
        'stats': stats,
        'title': 'Finance & Comptabilité',
        'search': search,
    })


@login_required
@role_required(['comptable', 'super_admin'])
def payment_create(request):
    school = request.user.school
    if request.method == 'POST':
        form = PaymentForm(request.POST, school=school)
        if form.is_valid():
            payment = form.save(commit=False)
            # Super Admin can work across schools; derive the tenant from the
            # selected student rather than allowing an unscoped payment.
            payment.school = school or payment.student.school
            payment.received_by = request.user
            # The official date is always assigned by the server.
            payment.payment_date = timezone.localdate()
            payment.save()
            log_action(request.user, 'CREATE', f"Paiement enregistré: {payment.student}", payment)
            messages.success(request, "Paiement enregistré.")
            return redirect('finance:index')
    else:
        form = PaymentForm(school=school)
    return render(request, 'finance/form.html', {'form': form, 'title': 'Nouveau paiement'})


@login_required
@role_required(['admin_ecole', 'comptable', 'super_admin'])
def payment_detail(request, pk):
    school = request.user.school
    payment = get_object_or_404(
        Payment.objects.select_related('student', 'fee_type', 'received_by'),
        pk=pk,
        **({'school': school} if school else {}),
    )
    return render(request, 'finance/detail.html', {
        'payment': payment,
        'title': 'Détails du paiement',
    })
