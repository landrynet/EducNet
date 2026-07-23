from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    path('', views.index, name='index'),
    path('years/', views.years, name='years'),
    path('years/create/', views.year_create, name='year_create'),
    path('classrooms/create/', views.classroom_create, name='classroom_create'),
    path('classrooms/<int:pk>/', views.classroom_detail, name='classroom_detail'),
    path('classrooms/<int:pk>/edit/', views.classroom_edit, name='classroom_edit'),
    path('subjects/create/', views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
]
