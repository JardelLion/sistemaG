
from .models import StockReference

def create_default_stock(sender, **kwargs):
    # Verifica se já existe um estoque padrão
    if not StockReference.objects.filter(name='Estoque Padrão').exists():
        StockReference.objects.create(
            name='Estoque Padrão',
            is_active=True,
            description='Este é o estoque criado automaticamente pelo sistema.'
        )
