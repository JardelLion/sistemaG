from django.db import models
import uuid
from django.contrib.auth.models import User

from people.models import Employee

# Create your models here.

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
