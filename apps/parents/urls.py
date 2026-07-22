from django.urls import path
from . import views

app_name = 'parents'

urlpatterns = [
    path('', views.parent_list, name='list'),
    path('create/', views.parent_create, name='create'),
    path('<int:pk>/edit/', views.parent_edit, name='edit'),
]
