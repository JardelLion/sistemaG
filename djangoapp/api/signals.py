from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Employee, Cart

@receiver(post_save, sender=Employee)
def create_cart_for_employee(sender, instance, created, **kwargs):
    if created:
        # Quando um novo funcionário for criado, crie um carrinho associado
        Cart.objects.create(user=instance.user)
