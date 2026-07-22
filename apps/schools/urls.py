from django.urls import path
from . import views

app_name = 'schools'

urlpatterns = [
    path('', views.school_list, name='list'),
    path('create/', views.school_create, name='create'),
    path('<int:pk>/credentials/', views.school_credentials, name='credentials'),
    path('<int:pk>/', views.school_detail, name='detail'),
    path('<int:pk>/edit/', views.school_edit, name='edit'),
    path('<int:pk>/toggle/', views.school_toggle, name='toggle'),
]
