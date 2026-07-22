from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('', views.staff_list, name='list'),
]
