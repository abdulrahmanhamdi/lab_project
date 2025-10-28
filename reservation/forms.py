from django import forms
from .models import Reservation, Student, Teacher, Laboratory, Computer
from django.contrib.auth.models import User

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['tarih', 'baslangic_saati', 'bitis_saati']
        widgets = {
            'tarih': forms.DateInput(attrs={'type': 'date'}),
            'baslangic_saati': forms.TimeInput(attrs={'type': 'time'}),
            'bitis_saati': forms.TimeInput(attrs={'type': 'time'}),
        }

class StudentCreationForm(forms.ModelForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    first_name = forms.CharField(label="First Name")
    last_name = forms.CharField(label="Last Name")

    class Meta:
        model = Student 
        fields = ['ogrenci_email'] 
        labels = {
            'ogrenci_email': 'Student Email '
        }

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )
        
        student = Student.objects.create(
            user=user,
            ogrenci_email=self.cleaned_data['ogrenci_email']
        )
        return student

class TeacherCreationForm(forms.ModelForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    first_name = forms.CharField(label="First Name")
    last_name = forms.CharField(label="Last Name")

    class Meta:
        model = Teacher
        fields = ['ogretmen_no']
        labels = {
            'ogretmen_no': 'Teacher ID'
        }

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )
        
        teacher = Teacher.objects.create(
            user=user,
            ogretmen_no=self.cleaned_data['ogretmen_no']
        )
        return teacher

class LaboratoryCreationForm(forms.ModelForm):
    managers = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(), 
        widget=forms.CheckboxSelectMultiple, 
        label="Managers (select one or more)",
        required=False
    )
    class Meta:
        model = Laboratory
        fields = ['lab_adi', 'kapasite', 'managers']
        labels = {
            'lab_adi': 'Laboratory Name',
            'kapasite': 'Capacity (Number of Computers)',
        }

class LabEditForm(forms.ModelForm):
    managers = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Managers (select one or more)",
        required=False 
    )

    class Meta:
        model = Laboratory
        fields = ['managers', 'operating_start_time', 'operating_end_time']
        labels = {
            'operating_start_time': 'Operating Start Time (e.g., 09:00)',
            'operating_end_time': 'Operating End Time (e.g., 17:00)',
        }
        widgets = {
            'operating_start_time': forms.TimeInput(attrs={'type': 'time'}),
            'operating_end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class TeacherReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['bilgisayar', 'tarih', 'baslangic_saati', 'bitis_saati']
        widgets = {
            'tarih': forms.DateInput(attrs={'type': 'date'}),
            'baslangic_saati': forms.TimeInput(attrs={'type': 'time'}),
            'bitis_saati': forms.TimeInput(attrs={'type': 'time'}),
        }
        labels = {
            'bilgisayar': 'Select Computer',
            'tarih': 'Date',
            'baslangic_saati': 'Start Time',
            'bitis_saati': 'End Time',
        }

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab', None)
        super().__init__(*args, **kwargs)

        if lab:
            self.fields['bilgisayar'].queryset = Computer.objects.filter(lab=lab)
