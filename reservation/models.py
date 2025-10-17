from django.db import models

# ---------------- Ogretmen (Teacher) Model ----------------
class Teacher(models.Model):
    ogretmen_no = models.CharField(max_length=50, unique=True, primary_key=True)
    ad = models.CharField(max_length=100)
    soyad = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    sifre = models.CharField(max_length=128) 

    def __str__(self):
        return f"{self.ad} {self.soyad}"

# ---------------- Laboratuvar (Laboratory) Model ----------------
class Laboratory(models.Model):
    lab_id = models.AutoField(primary_key=True)
    lab_adi = models.CharField(max_length=150)
    kapasite = models.IntegerField()
    sorumlu = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, to_field='ogretmen_no')

    def __str__(self):
        return self.lab_adi

# ---------------- Bilgisayar (Computer) Model ----------------
class Computer(models.Model):
    bilgisayar_id = models.AutoField(primary_key=True)
    lab = models.ForeignKey(Laboratory, on_delete=models.CASCADE)

    def __str__(self):
        return f"Computer No: {self.bilgisayar_id} in {self.lab.lab_adi}"

# ---------------- Ogrenci (Student) Model ----------------
class Student(models.Model):
    ogrenci_email = models.EmailField(unique=True, primary_key=True)
    ad = models.CharField(max_length=100)
    soyad = models.CharField(max_length=100)
    sifre = models.CharField(max_length=128) 

    def __str__(self):
        return self.ogrenci_email

# ---------------- Rezervasyon (Reservation) Model ----------------
class Reservation(models.Model):
    rezervasyon_id = models.AutoField(primary_key=True)
    ogrenci = models.ForeignKey(Student, on_delete=models.CASCADE)
    bilgisayar = models.ForeignKey(Computer, on_delete=models.CASCADE)
    tarih = models.DateField()
    baslangic_saati = models.TimeField()
    bitis_saati = models.TimeField()
    durum = models.CharField(max_length=50, default='Onaylandı') 

    def __str__(self):
        return f"Reservation for {self.ogrenci} on {self.tarih}"