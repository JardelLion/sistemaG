# api/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter # type: ignore
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ActionHistoryViewSet,
    AggregateSalesByDateViewSet,
    EmployeeViewSet,
    ProductViewSet,
    SaleViewSet,
   
    StockManagerViewSet,
    CustomTokenObtainPairView,
    SalesByEmployee,
    TotalStockValueView,
    TotalSalesValueView
  
   
)

# Configuração do roteador
router = DefaultRouter()
router.register(r'employees', EmployeeViewSet) # done
router.register(r'products', ProductViewSet) # done 
router.register(r'stockmanager', StockManagerViewSet) # done




router.register(r'sales', SaleViewSet)
router.register(r'sales-by-employee', SalesByEmployee, basename='sales-by-employee')
router.register(r'aggregate-sales-by-date', AggregateSalesByDateViewSet, basename='aggregate-sales-by-date')
router.register(r'action-history', ActionHistoryViewSet, basename='action-history')

# URLs adicionais
urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # Endpoint para obter token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # Endpoint para atualizar token
    path('total-stock-value/', TotalStockValueView.as_view(), name='total-stock-value'),
    path('total-sales/', TotalSalesValueView.as_view(), name='total-sales-value'),
    
]

# Adiciona as URLs do roteador ao urlpatterns
urlpatterns += router.urls
