from django.db import models
from django.contrib.auth.models import User

# ---------------- Teacher Model ----------------
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ogretmen_no = models.CharField(max_length=50, unique=True, primary_key=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

# ---------------- Laboratory Model ----------------
# في reservation/models.py
class Laboratory(models.Model):
    lab_id = models.AutoField(primary_key=True)
    lab_adi = models.CharField(max_length=150)
    kapasite = models.IntegerField()
    managers = models.ManyToManyField(
        User, 
        related_name='managed_labs',
        blank=True
    )

    operating_start_time = models.TimeField(null=True, blank=True)
    operating_end_time = models.TimeField(null=True, blank=True)
    # ------------------------------------

    def __str__(self):
        return self.lab_adi

# ---------------- Computer Model ----------------
class Computer(models.Model):
    bilgisayar_id = models.AutoField(primary_key=True)
    lab = models.ForeignKey(Laboratory, on_delete=models.CASCADE)

    computer_name = models.CharField(max_length=100) 

    def __str__(self):
        return f"{self.computer_name} (ID: {self.bilgisayar_id}) in {self.lab.lab_adi}"

# ---------------- Student Model ----------------
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ogrenci_email = models.EmailField(unique=True, primary_key=True)

    def __str__(self):
        return self.user.username

# ---------------- Reservation Model ----------------
class Reservation(models.Model):

    STATUS_CHOICES = [
        ('Beklemede', 'Pending'),
        ('Onaylandı', 'Approved'),
        ('Reddedildi', 'Rejected'),
    ]

    rezervasyon_id = models.AutoField(primary_key=True)
    ogrenci = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    bilgisayar = models.ForeignKey(Computer, on_delete=models.CASCADE)
    tarih = models.DateField()
    baslangic_saati = models.TimeField()
    bitis_saati = models.TimeField()

    durum = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='Beklemede'
    )

    def __str__(self):
        return f"Reservation for {self.ogrenci} on {self.tarih} ({self.get_durum_display()})"
