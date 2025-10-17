from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Laboratory, Computer, Student, Reservation
from .forms import ReservationForm
from django.utils import timezone

def lab_list(request):
    labs = Laboratory.objects.all()
    
    context = {
        'laboratories': labs
    }
    
    return render(request, 'reservation/lab_list.html', context)

def lab_detail(request, lab_id):
    lab = Laboratory.objects.get(pk=lab_id)
    
    computers_in_lab = Computer.objects.filter(lab=lab)
    
    context = {
        'laboratory': lab,
        'computers': computers_in_lab
    }
    
    return render(request, 'reservation/lab_detail.html', context)

def create_reservation(request, computer_id):
    computer = Computer.objects.get(pk=computer_id)
    
    student = Student.objects.first() 

    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.bilgisayar = computer
            reservation.ogrenci = student
            reservation.save()
            return redirect('lab_detail', lab_id=computer.lab.lab_id)
    else:
        form = ReservationForm()

    context = {
        'form': form,
        'computer': computer
    }
    return render(request, 'reservation/create_reservation.html', context)

def lab_detail(request, lab_id):
    lab = Laboratory.objects.get(pk=lab_id)
    computers_in_lab = Computer.objects.filter(lab=lab)
    
    today = timezone.now().date()
    reservations_today = Reservation.objects.filter(
        bilgisayar__in=computers_in_lab, 
        tarih=today
    )
    
    booked_computer_ids = [res.bilgisayar.bilgisayar_id for res in reservations_today]
    
    context = {
        'laboratory': lab,
        'computers': computers_in_lab,
        'booked_computer_ids': booked_computer_ids, 
    }
    
    return render(request, 'reservation/lab_detail.html', context)



def lab_detail(request, lab_id):
    lab = Laboratory.objects.get(pk=lab_id)
    computers_in_lab = Computer.objects.filter(lab=lab)
    
    today = timezone.now().date()
    reservations_today = Reservation.objects.filter(
        bilgisayar__in=computers_in_lab, 
        tarih=today
    )
    
    booked_computer_ids = [res.bilgisayar.bilgisayar_id for res in reservations_today]
    
    context = {
        'laboratory': lab,
        'computers': computers_in_lab,
        'booked_computer_ids': booked_computer_ids,
    }
    
    return render(request, 'reservation/lab_detail.html', context)

def my_reservations(request):
    student = Student.objects.first()
    
    reservations = Reservation.objects.filter(ogrenci=student).order_by('-tarih', '-baslangic_saati')
    
    context = {
        'reservations': reservations
    }
    
    return render(request, 'reservation/my_reservations.html', context)