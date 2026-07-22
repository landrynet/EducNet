from django.urls import path
from . import views

app_name = 'enrollment'

urlpatterns = [
    path('', views.enrollment_index, name='index'),
    path('create/', views.enrollment_create, name='create'),
]
