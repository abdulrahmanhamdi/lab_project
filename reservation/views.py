from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Teacher, Laboratory, Computer, Student, Reservation
from .forms import ReservationForm, StudentCreationForm, TeacherCreationForm, LaboratoryCreationForm, LabManagersForm \
,TeacherReservationForm
from django.db.models import Q, Sum
from datetime import datetime, timedelta
from django.contrib import messages 

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
    
    if request.method == 'POST':
        reservation_id = request.POST.get('reservation_id')
        reservation = get_object_or_404(Reservation, pk=reservation_id)
        
        # Check which button was clicked
        if 'approve_reservation' in request.POST:
            reservation.durum = 'Onaylandı'  # Approved
            reservation.save()
            
        elif 'reject_reservation' in request.POST:
            reservation.durum = 'Reddedildi'  # Rejected
            reservation.save()
            
        return redirect('teacher_dashboard')
    
    # Handle GET requests
    try:

        labs_managed = request.user.managed_labs.all()
        
        if not labs_managed.exists():
            raise Laboratory.DoesNotExist  # Does not manage any laboratory

        # 2. Retrieve pending reservations for *all* these laboratories
        computers_in_labs = Computer.objects.filter(lab__in=labs_managed)
        
        pending_reservations = Reservation.objects.filter(
            bilgisayar__in=computers_in_labs,
            durum='Beklemede'
        ).order_by('tarih', 'baslangic_saati')
        
        context = {
            'user': request.user,
            'labs': labs_managed,  # Send the list of laboratories
            'pending_reservations': pending_reservations
        }
        
    except (Laboratory.DoesNotExist):
        context = { 'user': request.user, 'labs': [], 'pending_reservations': [] }
        
    return render(request, 'reservation/teacher_dashboard.html', context)


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
            tarih = form.cleaned_data['tarih']
            baslangic_saati = form.cleaned_data['baslangic_saati']
            bitis_saati = form.cleaned_data['bitis_saati']

            time_overlap = Reservation.objects.filter(
                bilgisayar=computer,
                tarih=tarih,
                durum='Onaylandı'
            ).filter(
                Q(baslangic_saati__lt=bitis_saati, bitis_saati__gt=baslangic_saati)
            ).exists()

            if time_overlap:
                messages.error(request, 'Error: This computer is already booked and confirmed at this time. Please choose another time.')
                return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            try:
                start_time_obj = datetime.strptime(str(baslangic_saati), '%H:%M:%S')
                end_time_obj = datetime.strptime(str(bitis_saati), '%H:%M:%S')
                duration_new_reservation = (end_time_obj - start_time_obj).total_seconds() / 60
            except ValueError:
                messages.error(request, 'Time input error.')
                return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            student_reservations_today = Reservation.objects.filter(
                ogrenci=student,
                tarih=tarih,
                durum='Onaylandı'
            )

            total_duration_minutes = 0
            for res in student_reservations_today:
                duration = (datetime.combine(tarih, res.bitis_saati) - datetime.combine(tarih, res.baslangic_saati)).total_seconds() / 60
                total_duration_minutes += duration

            if (total_duration_minutes + duration_new_reservation) > 120:
                messages.error(request, 'Error: You have exceeded the maximum daily booking limit of two hours.')
                return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            other_lab_reservation = student_reservations_today.exclude(
                bilgisayar__lab=computer.lab
            ).exists()

            if other_lab_reservation:
                messages.error(request, 'Error: You cannot book in more than one lab on the same day.')
                return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            reservation = form.save(commit=False)
            reservation.bilgisayar = computer
            reservation.ogrenci = student
            reservation.save()

            messages.success(request, 'Reservation request submitted successfully and is now pending teacher approval.')
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

    managers_form = LabManagersForm(instance=lab)

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

        elif 'update_managers' in request.POST:
            managers_form = LabManagersForm(request.POST, instance=lab)
            if managers_form.is_valid():
                managers_form.save()  
            return redirect('admin_lab_detail', lab_id=lab.lab_id)

    computers_in_lab = Computer.objects.filter(lab=lab)

    context = {
        'lab': lab,
        'computers': computers_in_lab,
        'managers_form': managers_form, 
    }
    return render(request, 'reservation/admin_lab_detail.html', context)

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
        
        elif 'delete_reservation' in request.POST:
            reservation_id_to_delete = request.POST.get('reservation_id')
            try:
                res_to_delete = Reservation.objects.get(pk=reservation_id_to_delete)
                res_to_delete.delete()
            except Reservation.DoesNotExist:
                pass
            return redirect('admin_dashboard')

    all_students = Student.objects.all()
    all_teachers = Teacher.objects.all()
    all_labs = Laboratory.objects.all()
    all_reservations = Reservation.objects.all().order_by('-tarih', '-baslangic_saati')

    context = {
        'student_form': student_form,
        'teacher_form': teacher_form,
        'lab_form': lab_form,
        'students': all_students,
        'teachers': all_teachers,
        'labs': all_labs,
        'reservations': all_reservations,
    }
    return render(request, 'reservation/admin_dashboard.html', context)

@login_required
def teacher_lab_detail(request, lab_id):
    lab = get_object_or_404(Laboratory, pk=lab_id)

    if lab not in request.user.managed_labs.all():
        return redirect('teacher_dashboard')

    # 1. Initialize forms for GET
    managers_form = LabManagersForm(instance=lab)
    # 2. Pass the lab instance to the new reservation form
    teacher_res_form = TeacherReservationForm(lab=lab)

    if request.method == 'POST':

        if 'add_computer' in request.POST:
            # Add a new computer
            Computer.objects.create(lab=lab)
            return redirect('teacher_lab_detail', lab_id=lab.lab_id)

        elif 'delete_computer' in request.POST:
            # Delete a computer
            computer_id_to_delete = request.POST.get('computer_id')
            try:
                pc_to_delete = Computer.objects.get(pk=computer_id_to_delete)
                pc_to_delete.delete()
            except Computer.DoesNotExist:
                pass
            return redirect('teacher_lab_detail', lab_id=lab.lab_id)

        elif 'update_managers' in request.POST:
            # Update lab managers
            managers_form = LabManagersForm(request.POST, instance=lab)
            if managers_form.is_valid():
                managers_form.save()
            return redirect('teacher_lab_detail', lab_id=lab.lab_id)

        # 3. New code: Teacher makes a reservation
        elif 'create_teacher_reservation' in request.POST:
            teacher_res_form = TeacherReservationForm(request.POST, lab=lab)
            if teacher_res_form.is_valid():
                # (Later, add logic to check for time overlap)
                reservation = teacher_res_form.save(commit=False)
                reservation.ogrenci = None  # 4. No student associated
                reservation.durum = 'Onaylandı'  # 5. Automatically approved
                reservation.save()
            return redirect('teacher_lab_detail', lab_id=lab.lab_id)

    computers_in_lab = Computer.objects.filter(lab=lab)

    context = {
        'lab': lab,
        'computers': computers_in_lab,
        'managers_form': managers_form,
        'teacher_res_form': teacher_res_form,  # 6. Send the form to the template
    }
    return render(request, 'reservation/teacher_lab_detail.html', context)
