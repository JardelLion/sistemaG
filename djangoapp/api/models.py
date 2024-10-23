from django.db import models
from django.utils import timezone
import uuid
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Sum, Q
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save
import re

from django.contrib.auth.models import User

# Create your models here.

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    acquisition_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name

class ProductHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField()
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    acquisition_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    created_at = models.DateTimeField(default=timezone.now)
   

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



class Stock(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)  # Cada produto tem um estoque
    quantity = models.PositiveIntegerField(default=0)  # Quantidade no estoque
    acquisition_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Valor de aquisição
    available = models.BooleanField(default=False) 
    date_added = models.DateTimeField(auto_now_add=True)
    responsible_user = models.ForeignKey(Employee, on_delete=models.CASCADE)  # Usuário responsável

    def __str__(self):
        return f"{self.quantity} unidades de {self.product.name} em estoque"

    def save(self, *args, **kwargs):
        # Verifica se o produto já tem uma entrada no estoque
        if not self.pk and Stock.objects.filter(product=self.product).exists():
            raise ValueError(f"Estoque para o produto {self.product.name} já foi adicionado.")

        # Se for a primeira vez que o estoque é adicionado, subtrai a quantidade do produto
        if not self.pk:
            self.product.quantity -= self.quantity
            self.product.save()

        super().save(*args, **kwargs)



class Sale(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sale_quantity = models.PositiveIntegerField()  # Quantidade vendida
    date = models.DateField(auto_now_add=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.product.name} - {self.sale_quantity} unidades"

    def save(self, *args, **kwargs):
        # Verifica se há estoque suficiente
        try:
            stock = Stock.objects.get(product=self.product)
        except Stock.DoesNotExist:
            raise ValueError("Produto não encontrado no estoque.")
        
         # Verifica se o produto está disponível
        if not stock.available:
            raise ValueError(f"O produto {self.product.name} não está disponível para venda.")


        # Permite a venda se a quantidade a ser vendida for menor ou igual à quantidade disponível
        if self.sale_quantity > stock.quantity:
            raise ValueError("A quantidade vendida excede o estoque disponível.")

        # Diminui a quantidade no estoque
        stock.quantity -= self.sale_quantity
        stock.save()

        # Chama o método save padrão para registrar a venda
        super().save(*args, **kwargs)

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee  = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notificação para {self.employee.name}: {self.message}'



class LoginActivity(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)
    ip_address = models.GenericIPAddressField()


    def __str__(self):
        return f"{self.user.username} - {self.status} - {self.timestamp}"


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Cart {self.id} for {self.user.username}'

class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.product.name} ({self.quantity}) in {self.cart.id}'



class ActionHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    sale = models.ForeignKey(Sale, null=True, on_delete=models.CASCADE)
    action_date_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Ação: {self.action} por {self.employee.name}'

@receiver(post_save, sender=Sale)
def create_action_history(sender, instance, created, **kwargs):
    if created:
        ActionHistory.objects.get_or_create(
            employee=instance.employee,
            action=f'Venda realizada: {instance.product.name} - Quantidade: {instance.sale_quantity}',
            sale=instance
        )
