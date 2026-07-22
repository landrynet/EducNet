from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.finance_index, name='index'),
    path('payment/create/', views.payment_create, name='payment_create'),
    path('payment/<int:pk>/', views.payment_detail, name='payment_detail'),
]
