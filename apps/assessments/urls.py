from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    path('', views.assessment_index, name='index'),
    path('create/', views.assessment_create, name='create'),
]
