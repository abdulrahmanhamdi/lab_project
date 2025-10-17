from django.urls import path
from . import views

urlpatterns = [
    path('', views.lab_list, name='lab_list'),
    path('lab/<int:lab_id>/', views.lab_detail, name='lab_detail'),
    path('computer/<int:computer_id>/reserve/', views.create_reservation, name='create_reservation'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
]