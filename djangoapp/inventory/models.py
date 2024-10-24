from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone
import uuid
from people.models import Employee
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
