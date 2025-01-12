from django.db import models
import uuid
from people.models import Employee
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import uuid
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
    
# Create your models here.
class StockReference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)  # Nome do estoque
    description = models.TextField(blank=True, null=True)  # Descrição opcional
    is_active = models.BooleanField(null=False, default=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Data de criação
    updated_at = models.DateTimeField(auto_now=True)  # Última atualização

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_reference = models.ForeignKey(StockReference, on_delete=models.CASCADE) 
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    acquisition_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name
    


    
class ProductHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    stock_reference = models.ForeignKey(StockReference, on_delete=models.CASCADE) 
    acquisition_value = models.DecimalField(max_digits=10, decimal_places=2)
    product_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.acquisition_value:.2f}' 


class Sale(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_reference = models.ForeignKey(StockReference, on_delete=models.CASCADE) 
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sale_quantity = models.PositiveIntegerField()  # Quantidade vendida
    date = models.DateField(auto_now_add=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.product.name} - {self.sale_quantity} unidades"
    

    def save(self, *args, **kwargs):
        # Verifica se há estoque suficiente
        from orders.models import Stock
        try:
            stock_reference = StockReference.objects.filter(is_active=True).first()
            stock = Stock.objects.get(product=self.product, stock_reference=stock_reference.id)
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

        # Adiciona o histórico de vendas
        SaleHistory.objects.create(
            sale=self,
            product=self.product,
            product_name=self.product.name,
            product_price=self.product.price,  # Supondo que o Product tenha um campo de preço
            product_acquisition_value =self.product.acquisition_value,
            
            sale_quantity=self.sale_quantity,
            sale_total_value=self.product.price * self.sale_quantity,  # Preço total da venda

            employee=self.employee,
            employee_name=self.employee.name,
            employee_email=self.employee.user.email,
            employee_address=self.employee.address,
            stock_reference=self.stock_reference
        )


class SaleHistory(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, null=True, blank=True, related_name='history')
    stock_reference = models.ForeignKey(StockReference, on_delete=models.CASCADE)
    
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_acquisition_value = models.DecimalField(max_digits=10, decimal_places=2)

    
    sale_quantity = models.PositiveIntegerField()
    sale_total_value = models.DecimalField(max_digits=10, decimal_places=2)  # Preço total da venda
  
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    employee_name = models.CharField(max_length=255)
    employee_email = models.EmailField()
    employee_address = models.CharField(max_length=255)

    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Histórico de venda: {self.product_name} - {self.sale_quantity} unidades"


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
    

class Stock(models.Model):
    stock_reference = models.ForeignKey(StockReference, on_delete=models.CASCADE)  # Referência ao estoque ativo
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Um produto pode estar em vários estoques
    quantity = models.PositiveIntegerField(default=0)  # Quantidade no estoque
    available = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    responsible_user = models.ForeignKey(Employee, on_delete=models.CASCADE)  # Usuário responsável

    def __str__(self):
        return f"{self.quantity} unidades de {self.product.name} em estoque"

    def save(self, *args, **kwargs):
        # Atribui automaticamente o estoque ativo se não estiver definido
        if not self.stock_reference:
            self.stock_reference = StockReference.objects.filter(is_active=True).first()  # Pega o estoque ativo

        # Verifica se o produto já tem uma entrada no estoque
        if not self.pk and Stock.objects.filter(product=self.product, stock_reference=StockReference.objects.filter(is_active=True).first()).exists():
            raise ValueError(f"Estoque para o produto {self.product.name} já foi adicionado.")

        # Se for a primeira vez que o estoque é adicionado, subtrai a quantidade do produto
        if not self.pk:
            self.product.quantity -= self.quantity
            self.product.save()

        super().save(*args, **kwargs)

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_reference = models.ForeignKey(StockReference, on_delete=models.CASCADE)  # Referência ao estoque ativo
    employee  = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='notifications')
    product_description =  models.CharField(max_length=255)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notificação para {self.employee.name}: {self.message}'
