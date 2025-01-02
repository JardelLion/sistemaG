from django.contrib import admin

# Register your models here.
from people.models import Employee, EmployeeHistory
admin.site.register(Employee)
admin.site.register(EmployeeHistory)
