from django import forms
from .models import Reservation

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['tarih', 'baslangic_saati', 'bitis_saati']
        widgets = {
            'tarih': forms.DateInput(attrs={'type': 'date'}),
            'baslangic_saati': forms.TimeInput(attrs={'type': 'time'}),
            'bitis_saati': forms.TimeInput(attrs={'type': 'time'}),
        }