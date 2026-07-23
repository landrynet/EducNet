from django.urls import path
from . import views

app_name = 'schools'

urlpatterns = [
    path('', views.school_list, name='list'),
    path('settings/', views.school_settings, name='settings'),
    path('settings/matricule-preview/', views.matricule_preview, name='matricule_preview'),
    path('create/', views.school_create, name='create'),
    path('<int:pk>/credentials/', views.school_credentials, name='credentials'),
    path('<int:pk>/', views.school_detail, name='detail'),
    path('<int:pk>/edit/', views.school_edit, name='edit'),
    path('<int:pk>/toggle/', views.school_toggle, name='toggle'),
]
