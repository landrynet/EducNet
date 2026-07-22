from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.core.paginator import Paginator
from apps.authentication.decorators import role_required
from .models import Payment, FeeType
from apps.audit.utils import log_action
from django import forms


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'fee_type', 'amount_due', 'amount', 'payment_date', 'method', 'reference', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            from apps.students.models import Student
            self.fields['student'].queryset = Student.objects.filter(school=school, is_active=True)
            self.fields['fee_type'].queryset = FeeType.objects.filter(school=school)


@login_required
@role_required(['admin_ecole', 'comptable', 'super_admin'])
def finance_index(request):
    school = request.user.school
    payments = Payment.objects.filter(school=school).select_related('student', 'fee_type') if school else Payment.objects.all()
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
    })


@login_required
@role_required(['admin_ecole', 'comptable', 'super_admin'])
def payment_create(request):
    school = request.user.school
    if request.method == 'POST':
        form = PaymentForm(request.POST, school=school)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.school = school
            payment.received_by = request.user
            payment.save()
            log_action(request.user, 'CREATE', f"Paiement enregistré: {payment.student}", payment)
            messages.success(request, "Paiement enregistré.")
            return redirect('finance:index')
    else:
        form = PaymentForm(school=school)
    return render(request, 'finance/form.html', {'form': form, 'title': 'Nouveau paiement'})
