from django.db import models

# Create your models here.
import uuid
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Sum
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.models import User

# Create your models here.

class Employee(models.Model):
    MOVEMENT_CHOICES = [
        ('admin', 'admin'),
        ('employee', 'employee')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee")
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    address = models.TextField()
    role = models.CharField(max_length=100, choices=MOVEMENT_CHOICES)
   
    is_active = models.BooleanField(default=True)


    def __str__(self) -> str:
        return self.user.username
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_employee(self):
        return self.role == 'funcionario'
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def realized_sales(self):
        from orders.models import Sale
        return Sale.objects.filter(employee=self)
    
    def total_sales(self):
        total = self.realized_sales().aggregate(Sum('sale_quantity'))
        return total['sale_quantity__sum'] or 0

    def sales_report(self):
        sales = self.realized_sales()
        report = []
        for sale in sales:
            report.append({
                'product': sale.product.name,
                'quantity': sale.sale_quantity,
                'data': sale.date  
            })
        return report
    
    def clean(self):
        if not re.match(r'\d{9,15}$', self.contact):
            raise ValidationError("O campo de contato deve conter apenas números e ter entre 9 a 15 dígitos.")


class EmployeeHistory(models.Model):
    MOVEMENT_CHOICES = [
        ('admin', 'admin'),
        ('employee', 'employee')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="employee-history" )
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    address = models.TextField()
    role = models.CharField(max_length=100, choices=MOVEMENT_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name 
