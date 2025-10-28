from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Teacher, Laboratory, Computer, Student, Reservation
from .forms import ReservationForm, StudentCreationForm, TeacherCreationForm, LaboratoryCreationForm, LabEditForm \
,TeacherReservationForm
from django.db.models import Q, Sum
from datetime import datetime, timedelta
from django.contrib import messages 
from django.contrib.auth.models import User

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

        elif 'approve_reservation_admin' in request.POST:
            reservation_id = request.POST.get('reservation_id')
            try:
                res_to_update = Reservation.objects.get(pk=reservation_id)
                res_to_update.durum = 'Onaylandı'
                res_to_update.save()
            except Reservation.DoesNotExist:
                pass
            return redirect('admin_dashboard')

        elif 'reject_reservation_admin' in request.POST:
            reservation_id = request.POST.get('reservation_id')
            try:
                res_to_update = Reservation.objects.get(pk=reservation_id)
                res_to_update.durum = 'Reddedildi'
                res_to_update.save()
            except Reservation.DoesNotExist:
                pass
            return redirect('admin_dashboard')

        elif 'delete_reservation' in request.POST:
            reservation_id_to_delete = request.POST.get('reservation_id')
            try:
                res_to_delete = Reservation.objects.get(pk=reservation_id_to_delete)
                res_to_delete.delete()
            except Reservation.DoesNotExist:
                pass
            return redirect('admin_dashboard')

        elif 'delete_student' in request.POST:
            user_id_to_delete = request.POST.get('user_id')
            try:
                user_to_delete = User.objects.get(pk=user_id_to_delete)
                user_to_delete.delete()
            except User.DoesNotExist:
                pass
            return redirect('admin_dashboard')

        elif 'delete_teacher' in request.POST:
            user_id_to_delete = request.POST.get('user_id')
            try:
                user_to_delete = User.objects.get(pk=user_id_to_delete)
                user_to_delete.delete()
            except User.DoesNotExist:
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


# ------------------- 3. Teacher Views -------------------

@login_required
def teacher_dashboard(request):
    if request.method == 'POST':
        reservation_id = request.POST.get('reservation_id')
        reservation = get_object_or_404(Reservation, pk=reservation_id)
        
        if 'approve_reservation' in request.POST:
            reservation.durum = 'Onaylandı'
            reservation.save()
            
        elif 'reject_reservation' in request.POST:
            reservation.durum = 'Reddedildi'
            reservation.save()
            
        return redirect('teacher_dashboard')
    
    try:
        labs_managed = request.user.managed_labs.all()
        
        if not labs_managed.exists():
            raise Laboratory.DoesNotExist

        computers_in_labs = Computer.objects.filter(lab__in=labs_managed)
        
        all_reservations_in_labs = Reservation.objects.filter(
            bilgisayar__in=computers_in_labs
        ).order_by('-tarih', '-baslangic_saati')

        pending_reservations = all_reservations_in_labs.filter(durum='Beklemede')
        approved_reservations = all_reservations_in_labs.filter(durum='Onaylandı')
        rejected_reservations = all_reservations_in_labs.filter(durum='Reddedildi')

        context = {
            'user': request.user,
            'labs': labs_managed,
            'pending_reservations': pending_reservations,
            'approved_reservations': approved_reservations,
            'rejected_reservations': rejected_reservations,
        }
        
    except (Laboratory.DoesNotExist, AttributeError):
        context = { 
            'user': request.user, 
            'labs': [], 
            'pending_reservations': [],
            'approved_reservations': [],
            'rejected_reservations': [],
        }

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
    # Only allow logged-in users who are students
    if not hasattr(request.user, 'student'):
        return redirect('login')

    computer = get_object_or_404(Computer, pk=computer_id)
    student = request.user.student

    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            # Extract data from the form
            date = form.cleaned_data['tarih']
            start_time = form.cleaned_data['baslangic_saati']
            end_time = form.cleaned_data['bitis_saati']

            # -----------------------------------------------------------
            # Condition 1: Prevent overlapping reservations on the same computer
            # -----------------------------------------------------------
            time_overlap = Reservation.objects.filter(
                bilgisayar=computer,
                tarih=date,
                durum='Onaylandı'  # Only check confirmed reservations
            ).filter(
                Q(baslangic_saati__lt=end_time, bitis_saati__gt=start_time)
            ).exists()

            if time_overlap:
                messages.error(request, 'Error: This computer is already booked at this time. Please choose another time.')
                return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            # -----------------------------------------------------------
            # Condition 2: Validate the time format and calculate duration
            # -----------------------------------------------------------
            try:
                start_time_obj = datetime.strptime(str(start_time), '%H:%M:%S')
                end_time_obj = datetime.strptime(str(end_time), '%H:%M:%S')
                duration_new_reservation = (end_time_obj - start_time_obj).total_seconds() / 60
            except ValueError:
                messages.error(request, 'Error: Invalid time input.')
                return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            # -----------------------------------------------------------
            # Condition 3: Check if student exceeds 2 hours total per day
            # -----------------------------------------------------------
            student_reservations_today = Reservation.objects.filter(
                ogrenci=student,
                tarih=date,
                durum='Onaylandı'
            )

            total_duration_minutes = 0
            for res in student_reservations_today:
                duration = (datetime.combine(date, res.bitis_saati) - datetime.combine(date, res.baslangic_saati)).total_seconds() / 60
                total_duration_minutes += duration

            if (total_duration_minutes + duration_new_reservation) > 120:
                messages.error(request, 'Error: You have exceeded the daily limit of 2 hours per day.')
                return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            # -----------------------------------------------------------
            # Condition 4: Ensure student can book only one lab per day
            # -----------------------------------------------------------
            other_lab_reservation = student_reservations_today.exclude(
                bilgisayar__lab=computer.lab
            ).exists()

            if other_lab_reservation:
                messages.error(request, 'Error: You cannot book in more than one lab on the same day.')
                return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            # -----------------------------------------------------------
            # Condition 5: Enforce lab working hours limits
            # -----------------------------------------------------------
            lab = computer.lab
            if lab.operating_start_time and lab.operating_end_time:
                if (start_time < lab.operating_start_time) or (end_time > lab.operating_end_time):
                    messages.error(request, f'Error: Reservation must be within lab working hours ({lab.operating_start_time} - {lab.operating_end_time}).')
                    return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            # -----------------------------------------------------------
            # If all checks pass → Save the reservation
            # -----------------------------------------------------------
            reservation = form.save(commit=False)
            reservation.bilgisayar = computer
            reservation.ogrenci = student
            reservation.save()

            messages.success(request, 'Reservation request submitted successfully. It is now pending teacher approval.')
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
def admin_lab_detail(request, lab_id):
    if not request.user.is_superuser:
        return redirect('login')

    lab = get_object_or_404(Laboratory, pk=lab_id)
    lab_edit_form = LabEditForm(instance=lab)

    if request.method == 'POST':
        if 'add_computer' in request.POST:
            new_computer_name = request.POST.get('computer_name')
            if new_computer_name:
                Computer.objects.create(lab=lab, computer_name=new_computer_name)
            return redirect('admin_lab_detail', lab_id=lab.lab_id)

        elif 'delete_computer' in request.POST:
            computer_id_to_delete = request.POST.get('computer_id')
            try:
                pc_to_delete = Computer.objects.get(pk=computer_id_to_delete)
                pc_to_delete.delete()
            except Computer.DoesNotExist:
                pass
            return redirect('admin_lab_detail', lab_id=lab.lab_id)

        elif 'update_lab_settings' in request.POST:
            lab_edit_form = LabEditForm(request.POST, instance=lab)
            if lab_edit_form.is_valid():
                lab_edit_form.save() 
            return redirect('admin_lab_detail', lab_id=lab.lab_id)

    computers_in_lab = Computer.objects.filter(lab=lab)

    context = {
        'lab': lab,
        'computers': computers_in_lab,
        'lab_edit_form': lab_edit_form,
    }
    return render(request, 'reservation/admin_lab_detail.html', context)

@login_required
def teacher_lab_detail(request, lab_id):
    lab = get_object_or_404(Laboratory, pk=lab_id)
    
    if lab not in request.user.managed_labs.all():
        return redirect('teacher_dashboard')
        
    lab_edit_form = LabEditForm(instance=lab)
    teacher_res_form = TeacherReservationForm(lab=lab) 

    if request.method == 'POST':
        if 'add_computer' in request.POST:
            new_computer_name = request.POST.get('computer_name')
            if new_computer_name:
                Computer.objects.create(lab=lab, computer_name=new_computer_name)
            return redirect('teacher_lab_detail', lab_id=lab.lab_id)
        
        elif 'delete_computer' in request.POST:
            computer_id_to_delete = request.POST.get('computer_id')
            try:
                pc_to_delete = Computer.objects.get(pk=computer_id_to_delete)
                pc_to_delete.delete()
            except Computer.DoesNotExist:
                pass
            return redirect('teacher_lab_detail', lab_id=lab.lab_id)
        
        elif 'update_lab_settings' in request.POST:
            lab_edit_form = LabEditForm(request.POST, instance=lab)
            if lab_edit_form.is_valid():
                lab_edit_form.save() 
            return redirect('teacher_lab_detail', lab_id=lab.lab_id)
        
        elif 'create_teacher_reservation' in request.POST:
            teacher_res_form = TeacherReservationForm(request.POST, lab=lab)
            if teacher_res_form.is_valid():
                reservation = teacher_res_form.save(commit=False)
                reservation.ogrenci = None
                reservation.durum = 'Onaylandı'
                reservation.save()
            return redirect('teacher_lab_detail', lab_id=lab.lab_id)

    computers_in_lab = Computer.objects.filter(lab=lab)
    
    context = {
        'lab': lab,
        'computers': computers_in_lab,
        'lab_edit_form': lab_edit_form, 
        'teacher_res_form': teacher_res_form,
    }
    return render(request, 'reservation/teacher_lab_detail.html', context)