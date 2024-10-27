from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import StockManagerViewSet, TotalSalesAndAcquisitionValueView, SaleViewSet
from orders.views import SalesByEmployeeWithIdViewSet
from .views import AggregateSalesByDateViewSet, SalesByEmployee, ProductViewSet

from .views import CartViewSet
from .views import CartItemsView
from .views import TotalProductValueView
from .views import employee_notifications, mark_as_read


router = DefaultRouter()

router.register(r'stockmanager', StockManagerViewSet) # done
router.register(r'products', ProductViewSet) # done 
router.register(r'sales', SaleViewSet, basename="sales")
router.register(r'aggregate-sales-by-date', AggregateSalesByDateViewSet, basename='aggregate-sales-by-date')
router.register(r'sales-by-employee', SalesByEmployee, basename='sales-by-employee')



# Inclui as URLs do router
urlpatterns = [
    path('', include(router.urls)),
    path('static-value/', TotalSalesAndAcquisitionValueView.as_view(), name='total-sales-value'),
    path("employee/<uuid:id>/sales/", SalesByEmployeeWithIdViewSet.as_view({'get': 'list'})),
    path('cart/', CartViewSet.as_view({'get': 'list'})),
    path('cart/add/', CartViewSet.as_view({'post': 'add_to_cart'})),
    path('cart/remove/<uuid:pk>/', CartViewSet.as_view({'delete': 'remove_from_cart'})),
    path('cart/items/<uuid:employee_id>/', CartItemsView.as_view(), name='cart-items') ,
    path('total-product-value/', TotalProductValueView.as_view(), name='total-stock-value'),
    path('notifications/', employee_notifications, name='employee_notifications'),
    path('api/notifications/<uuid:notification_id>/read/', mark_as_read, name='mark_as_read'),

]