from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    path('', views.index, name='index'),
    path('years/', views.years, name='years'),
    path('years/create/', views.year_create, name='year_create'),
    path('classrooms/create/', views.classroom_create, name='classroom_create'),
    path('subjects/create/', views.subject_create, name='subject_create'),
]
