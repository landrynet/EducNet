from django.urls import path
from . import views

app_name = 'backup'

urlpatterns = [
    path('', views.backup_index, name='index'),
    path('create/', views.backup_create, name='create'),
]
