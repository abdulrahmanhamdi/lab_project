from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Teacher, Laboratory, Computer, Student, Reservation
from .forms import ReservationForm, StudentCreationForm, TeacherCreationForm, LaboratoryCreationForm

# ------------------- 1. Authentication & Role Routing -------------------

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # --- New role-based routing logic ---
                
                # 1. Admin/Superuser
                if user.is_superuser:
                    return redirect('admin_dashboard')
                
                # 2. Teacher
                elif hasattr(user, 'teacher'):
                    return redirect('teacher_dashboard')
                
                # 3. Student
                elif hasattr(user, 'student'):
                    return redirect('lab_list')
                
                else:
                    return redirect('login')
    else:
        form = AuthenticationForm()
    return render(request, 'reservation/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ------------------- 2. Admin Views -------------------

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('login')
    return render(request, 'reservation/admin_dashboard.html')


# ------------------- 3. Teacher Views -------------------

@login_required
def teacher_dashboard(request):
    if not hasattr(request.user, 'teacher'):
        return redirect('login')
    return render(request, 'reservation/teacher_dashboard.html')


# ------------------- 4. Student Views -------------------

@login_required
def lab_list(request):
    if not hasattr(request.user, 'student'):
        return redirect('login')
        
    labs = Laboratory.objects.all()
    context = {
        'laboratories': labs
    }
    return render(request, 'reservation/lab_list.html', context)


@login_required
def lab_detail(request, lab_id):
    if not hasattr(request.user, 'student'):
        return redirect('login')
        
    lab = get_object_or_404(Laboratory, pk=lab_id)
    computers_in_lab = Computer.objects.filter(lab=lab)
    
    today = timezone.now().date()
    reservations_today = Reservation.objects.filter(
        bilgisayar__in=computers_in_lab, 
        tarih=today,
        durum='Onaylandı'
    )
    
    booked_computer_ids = [res.bilgisayar.bilgisayar_id for res in reservations_today]
    
    context = {
        'laboratory': lab,
        'computers': computers_in_lab,
        'booked_computer_ids': booked_computer_ids,
    }
    return render(request, 'reservation/lab_detail.html', context)


@login_required
def create_reservation(request, computer_id):
    if not hasattr(request.user, 'student'):
        return redirect('login')

    computer = get_object_or_404(Computer, pk=computer_id)
    student = request.user.student 
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.bilgisayar = computer
            reservation.ogrenci = student
            reservation.save()
            return redirect('my_reservations')
    else:
        form = ReservationForm()

    context = {
        'form': form,
        'computer': computer
    }
    return render(request, 'reservation/create_reservation.html', context)


@login_required
def my_reservations(request):
    if not hasattr(request.user, 'student'):
        return redirect('login')
    
    student = request.user.student
    
    reservations = Reservation.objects.filter(ogrenci=student).order_by('-tarih', '-baslangic_saati')
    
    context = {
        'reservations': reservations
    }
    return render(request, 'reservation/my_reservations.html', context)

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('login')

    if request.method == 'POST':
        form = StudentCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard') 
    else:
        form = StudentCreationForm()


    all_students = Student.objects.all()

    context = {
        'student_form': form,
        'students': all_students,
    }
    return render(request, 'reservation/admin_dashboard.html', context)


@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('login')

    student_form = StudentCreationForm()
    teacher_form = TeacherCreationForm()

    if request.method == 'POST':
        if 'create_student' in request.POST:
            student_form = StudentCreationForm(request.POST)
            if student_form.is_valid():
                student_form.save()
                return redirect('admin_dashboard')
        
        elif 'create_teacher' in request.POST:
            teacher_form = TeacherCreationForm(request.POST)
            if teacher_form.is_valid():
                teacher_form.save()
                return redirect('admin_dashboard')

    all_students = Student.objects.all()
    all_teachers = Teacher.objects.all()

    context = {
        'student_form': student_form,
        'teacher_form': teacher_form,
        'students': all_students,
        'teachers': all_teachers,
    }
    return render(request, 'reservation/admin_dashboard.html', context)

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('login')

    student_form = StudentCreationForm()
    teacher_form = TeacherCreationForm()
    lab_form = LaboratoryCreationForm()

    if request.method == 'POST':
        if 'create_student' in request.POST:
            student_form = StudentCreationForm(request.POST)
            if student_form.is_valid():
                student_form.save()
                return redirect('admin_dashboard')
        
        elif 'create_teacher' in request.POST:
            teacher_form = TeacherCreationForm(request.POST)
            if teacher_form.is_valid():
                teacher_form.save()
                return redirect('admin_dashboard')
        
        elif 'create_lab' in request.POST:
            lab_form = LaboratoryCreationForm(request.POST)
            if lab_form.is_valid():
                lab_form.save()
                return redirect('admin_dashboard')

    all_students = Student.objects.all()
    all_teachers = Teacher.objects.all()
    all_labs = Laboratory.objects.all()

    context = {
        'student_form': student_form,
        'teacher_form': teacher_form,
        'lab_form': lab_form,
        'students': all_students,
        'teachers': all_teachers,
        'labs': all_labs,
    }
    return render(request, 'reservation/admin_dashboard.html', context)

@login_required
def admin_lab_detail(request, lab_id):
    if not request.user.is_superuser:
        return redirect('login')
        
    lab = get_object_or_404(Laboratory, pk=lab_id)
    
    if request.method == 'POST':
        if 'add_computer' in request.POST:
            Computer.objects.create(lab=lab)
            return redirect('admin_lab_detail', lab_id=lab.lab_id)
        
        elif 'delete_computer' in request.POST:
            computer_id_to_delete = request.POST.get('computer_id')
            try:
                pc_to_delete = Computer.objects.get(pk=computer_id_to_delete)
                pc_to_delete.delete()
            except Computer.DoesNotExist:
                pass
            return redirect('admin_lab_detail', lab_id=lab.lab_id)
        
    computers_in_lab = Computer.objects.filter(lab=lab)
    
    context = {
        'lab': lab,
        'computers': computers_in_lab
    }
    return render(request, 'reservation/admin_lab_detail.html', context)
