from django.apps import AppConfig
from django.db.models.signals import post_migrate


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        import orders.signals
    
