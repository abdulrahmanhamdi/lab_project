from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_landing_view, name='login_landing'),
    path('login/student/', views.login_student_view, name='login_student'),
    path('login/teacher/', views.login_teacher_view, name='login_teacher'),
    path('login/admin/', views.login_admin_view, name='login_admin'),    
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher-dashboard/lab/<int:lab_id>/', views.teacher_lab_detail, name='teacher_lab_detail'),    
    path('admin-dashboard/lab/<int:lab_id>/', views.admin_lab_detail, name='admin_lab_detail'),
    path('admin-dashboard/reset-password/<int:user_id>/', views.admin_reset_password_view, name='admin_reset_password'),

    path('', views.lab_list, name='lab_list'),
    path('lab/<int:lab_id>/', views.lab_detail, name='lab_detail'),
    path('computer/<int:computer_id>/reserve/', views.create_reservation, name='create_reservation'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
]