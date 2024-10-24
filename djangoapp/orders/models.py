from django.db import models
import uuid
from people.models import Employee
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import uuid
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
        from orders.models import Stock
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

        # Adiciona o histórico de vendas
        SaleHistory.objects.create(
            sale=self,
            
            product=self.product,
            product_name=self.product.name,
            product_price=self.product.price,  # Supondo que o Product tenha um campo de preço
            product_acquistion_value =self.product.acquisition_value,
            
            sale_quantity=self.sale_quantity,
            sale_price=self.product.price * self.sale_quantity,  # Preço total da venda

            employee=self.employee,
            employee_name=self.employee.name,
            employee_email=self.employee.user.email,
            employee_address=self.employee.address
        )


class SaleHistory(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, null=True, blank=True, related_name='history')
    
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_acquisition_value = models.DecimalField(max_digits=10, decimal_places=2)

    
    sale_quantity = models.PositiveIntegerField()
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)  # Preço total da venda
   
    
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    employee_name = models.CharField(max_length=255)
    employee_email = models.EmailField()
    employee_address = models.CharField(max_length=255)

    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Histórico de venda: {self.product_name} - {self.sale_quantity} unidades"


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
