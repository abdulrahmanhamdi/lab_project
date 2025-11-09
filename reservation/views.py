from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Teacher, Laboratory, Computer, Student, Reservation
from .forms import ReservationForm, StudentCreationForm, TeacherCreationForm, LaboratoryCreationForm, LabEditForm
from django.db.models import Q, Sum
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm


# ------------------- 1. Authentication & Role Routing -------------------

@login_required
def change_password_view(request):
    if request.method == 'POST':
        # 1. Use the built-in form and pass the current user
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()  # 2. Automatically saves with proper hashing

            # 3. (Very important) Update the session with the new password
            update_session_auth_hash(request, user)

            messages.success(request, 'Password changed successfully!')
            return redirect('change_password')  # Reload the same page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'reservation/change_password.html', {
        'form': form
    })
#------------------- Admin Reset Password View -------------------
@login_required
def admin_reset_password_view(request, user_id):
    # 1. Ensure that the current user is an admin
    if not request.user.is_superuser:
        return redirect('login')

    # 2. Get the target user (whose password will be reset)
    user_to_reset = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        # 3. Use the built-in SetPasswordForm
        form = SetPasswordForm(user_to_reset, request.POST)
        if form.is_valid():
            form.save()  # 4. Automatically saves with proper password hashing
            messages.success(request, f'Password for user {user_to_reset.username} has been successfully changed.')
            return redirect('admin_dashboard')  # Redirect back to admin dashboard
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SetPasswordForm(user_to_reset)

    return render(request, 'reservation/admin_reset_password.html', {
        'form': form,
        'user_to_reset': user_to_reset
    })
#------------------- Login Views -------------------
#1. Landing page (just buttons) ---
def login_landing_view(request):
    return render(request, 'reservation/login_landing.html')


#2. Student Login Page ---
def login_student_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # --- Check role ---
            if hasattr(user, 'student') and not user.managed_labs.exists():
                login(request, user)
                return redirect('lab_list')
            else:
                messages.error(request, 'This account is not a regular student account.')
    else:
        form = AuthenticationForm()

    return render(request, 'reservation/login_form.html', {
        'form': form,
        'title': 'Student Login'
    })


#3. Teacher / Assistant Login Page ---
def login_teacher_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # --- Check role ---
            if user.managed_labs.exists():
                login(request, user)
                return redirect('teacher_dashboard')
            else:
                messages.error(request, 'This account does not have lab manager privileges.')
    else:
        form = AuthenticationForm()

    return render(request, 'reservation/login_form.html', {
        'form': form,
        'title': 'Teacher / Assistant Login'
    })


#4. Admin Login Page ---
def login_admin_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # --- Check role ---
            if user.is_superuser:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'This account is not a system administrator.')
    else:
        form = AuthenticationForm()

    return render(request, 'reservation/login_form.html', {
        'form': form,
        'title': 'Admin Login'
    })


def logout_view(request):
    logout(request)
    return redirect('login_landing')


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

        elif 'delete_lab' in request.POST:
            lab_id_to_delete = request.POST.get('lab_id')
            try:
                lab_to_delete = Laboratory.objects.get(pk=lab_id_to_delete)
                lab_to_delete.delete()
            except Laboratory.DoesNotExist:
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
    if not request.user.managed_labs.exists() and not request.user.is_superuser:
        return redirect('login')

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
    context = {'laboratories': labs}
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

            pending_or_approved = ['Onaylandı', 'Beklemede']

            time_overlap = Reservation.objects.filter(
                bilgisayar=computer,
                tarih=tarih,
                durum__in=pending_or_approved
            ).filter(
                Q(baslangic_saati__lt=bitis_saati, bitis_saati__gt=baslangic_saati)
            ).exists()

            if time_overlap:
                messages.error(request, 'This computer is already reserved for the selected time.')
                return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            student_reservations_today = Reservation.objects.filter(
                ogrenci=student,
                tarih=tarih,
                durum__in=pending_or_approved
            )

            try:
                start_time_obj = datetime.strptime(str(baslangic_saati), '%H:%M:%S')
                end_time_obj = datetime.strptime(str(bitis_saati), '%H:%M:%S')
                duration_new_reservation = (end_time_obj - start_time_obj).total_seconds() / 60

                if duration_new_reservation <= 0:
                    messages.error(request, 'End time must be after start time.')
                    return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            except ValueError:
                messages.error(request, 'Invalid time format.')
                return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            total_duration_minutes = 0
            for res in student_reservations_today:
                duration = (datetime.combine(tarih, res.bitis_saati) -
                            datetime.combine(tarih, res.baslangic_saati)).total_seconds() / 60
                total_duration_minutes += duration

            if (total_duration_minutes + duration_new_reservation) > 120:
                messages.error(request, 'You exceeded the daily maximum reservation limit (2 hours).')
                return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            other_lab_reservation = student_reservations_today.exclude(
                bilgisayar__lab=computer.lab
            ).exists()

            if other_lab_reservation:
                messages.error(request, 'You can reserve only one lab per day.')
                return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            lab = computer.lab
            if lab.operating_start_time and lab.operating_end_time:
                if (baslangic_saati < lab.operating_start_time) or (bitis_saati > lab.operating_end_time):
                    messages.error(
                        request,
                        f'Reservation times must be within lab operating hours ({lab.operating_start_time} - {lab.operating_end_time}).'
                    )
                    return redirect('create_reservation', computer_id=computer.bilgisayar_id)

            reservation = form.save(commit=False)
            reservation.bilgisayar = computer
            reservation.ogrenci = student
            reservation.save()

            messages.success(request, 'Your reservation request has been sent for approval.')
            return redirect('my_reservations')

    else:
        form = ReservationForm()

    context = {'form': form, 'computer': computer}
    return render(request, 'reservation/create_reservation.html', context)


@login_required
def my_reservations(request):
    if not hasattr(request.user, 'student'):
        return redirect('login')

    student = request.user.student
    reservations = Reservation.objects.filter(ogrenci=student).order_by('-tarih', '-baslangic_saati')

    context = {'reservations': reservations}
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

    computers_in_lab = Computer.objects.filter(lab=lab)

    context = {
        'lab': lab,
        'computers': computers_in_lab,
        'lab_edit_form': lab_edit_form,
    }
    return render(request, 'reservation/teacher_lab_detail.html', context)
