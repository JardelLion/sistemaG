# your_app/management/commands/archive_old_sales.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from orders.models import Sale

class Command(BaseCommand):
    help = 'Archive all sales by setting is_archived to True.'

    def handle(self, *args, **kwargs):
        # Arquivar todas as vendas que não estão arquivadas
        archived_sales_count = Sale.objects.filter(is_archived=False).update(is_archived=True, archived_at=timezone.now())

        if archived_sales_count > 0:
            self.stdout.write(self.style.SUCCESS(f"{archived_sales_count} vendas arquivadas com sucesso."))
        else:
            self.stdout.write(self.style.WARNING("Nenhuma venda encontrada para arquivamento."))
