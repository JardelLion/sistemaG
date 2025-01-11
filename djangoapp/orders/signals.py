from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Employee, StockReference
from django.contrib.auth.models import UserManager
from django.utils.crypto import get_random_string

@receiver(post_migrate)
def create_default_records(sender, **kwargs):
    # Verifica se já existe um estoque padrão
    if not StockReference.objects.filter(name='Estoque Padrão').exists():
        StockReference.objects.create(
            name='Estoque Padrão',
            is_active=True,
            description='Este é o estoque criado automaticamente pelo sistema.'
        )
    
    # Verifica se já existe um funcionário padrão
    if not Employee.objects.filter(name='Funcionário Padrão').exists():
        # Verifica se já existe um usuário padrão
        if not User.objects.filter(username='Saide Marrapaz').exists():
            # Cria o usuário padrão
            user = User.objects.create_user(
                username='Saide Marrapaz',  # Nome de usuário modificado
                password='603684',  # Senha padrão
            )

            # Cria o Employee padrão
            Employee.objects.create(
                user=user,
                name='Saide Marrapaz A',
                contact='+244 943919317',  # Contato padrão
                address='Endereço Padrão',
                role='admin',
                is_active=True,
                stock_reference=StockReference.objects.get(name='Estoque Padrão')  # Associa ao estoque padrão
            )
