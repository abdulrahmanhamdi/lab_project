from django.contrib import admin
from .models import Teacher, Laboratory, Computer, Student, Reservation

# Register your models here.
admin.site.register(Teacher)
admin.site.register(Laboratory)
admin.site.register(Computer)
admin.site.register(Student)
admin.site.register(Reservation)