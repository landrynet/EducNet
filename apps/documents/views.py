from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from apps.authentication.decorators import role_required
from .models import Document, DocumentCategory
from django import forms


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'category', 'file', 'student']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['category'].queryset = DocumentCategory.objects.filter(school=school)
            from apps.students.models import Student
            self.fields['student'].queryset = Student.objects.filter(school=school)
            self.fields['student'].required = False


@login_required
def documents_index(request):
    school = request.user.school
    docs = Document.objects.filter(school=school, is_active=True).select_related('category', 'student') if school else Document.objects.none()
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, school=school)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.school = school
            doc.uploaded_by = request.user
            doc.save()
            messages.success(request, "Document ajouté.")
            return redirect('documents:index')
    else:
        form = DocumentForm(school=school)
    paginator = Paginator(docs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'documents/index.html', {'page_obj': page, 'form': form, 'title': 'Documents & Archives'})
