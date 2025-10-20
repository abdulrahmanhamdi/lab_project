from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('admin-dashboard/lab/<int:lab_id>/', views.admin_lab_detail, name='admin_lab_detail'),

    path('', views.lab_list, name='lab_list'),
    path('lab/<int:lab_id>/', views.lab_detail, name='lab_detail'),
    path('computer/<int:computer_id>/reserve/', views.create_reservation, name='create_reservation'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
]