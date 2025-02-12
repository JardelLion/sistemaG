from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import StockManagerViewSet, TotalSalesAndAcquisitionValueView, SaleViewSet
from orders.views import SalesByEmployeeWithIdViewSet
from .views import AggregateSalesByDateViewSet, SalesByEmployee, ProductViewSet

from .views import CartViewSet
from .views import CartItemsView
from .views import TotalProductValueView
from .views import employee_notifications, mark_as_read
from .views import StockReferenceViewSet
from .views import generate_employee_report
from .views import UpdateEmployeeSector



router = DefaultRouter()

router.register(r'stockmanager', StockManagerViewSet) # done
router.register(r'products', ProductViewSet) # done 
router.register(r'sales', SaleViewSet, basename="sales")
router.register(r'aggregate-sales-by-date', AggregateSalesByDateViewSet, basename='aggregate-sales-by-date')
router.register(r'sales-by-employee', SalesByEmployee, basename='sales-by-employee')
router.register(r'create-stock', StockReferenceViewSet, basename='create a stock')
router.register(r'stock-references', StockReferenceViewSet, basename='stockreference')



# Inclui as URLs do router
urlpatterns = [
    path('', include(router.urls)),
    # URL patterns para endpoints específicos

    path('stock-reference/<uuid:pk>/activate/', StockReferenceViewSet.as_view({'post': 'activate'}), name='stock-reference-activate'),
    path('stock-reference/<uuid:pk>/deactivate/', StockReferenceViewSet.as_view({'post': 'deactivate'}), name='stock-reference-deactivate'),
    path('stock-reference/<uuid:pk>/delete/', StockReferenceViewSet.as_view({'delete': 'destroy'}), name='stock-reference-delete'),
    path('static-value/', TotalSalesAndAcquisitionValueView.as_view(), name='total-sales-value'),
    path("employee/<uuid:id>/sales/", SalesByEmployeeWithIdViewSet.as_view({'get': 'list'})),
    path('cart/', CartViewSet.as_view({'get': 'list'})),
    path('cart/add/', CartViewSet.as_view({'post': 'add_to_cart'})),
    path('cart/remove/<uuid:pk>/', CartViewSet.as_view({'delete': 'remove_from_cart'})),
    path('cart/items/<uuid:employee_id>/', CartItemsView.as_view(), name='cart-items') ,
    path('total-product-value/', TotalProductValueView.as_view(), name='total-stock-value'),
    path('notifications/', employee_notifications, name='employee_notifications'),
    path('api/notifications/<uuid:notification_id>/read/', mark_as_read, name='mark_as_read'),
    path('generate-report/', generate_employee_report, name='generate_employee_report'),
    path('employee/<uuid:employee_id>/sector', UpdateEmployeeSector.as_view(), name='update-employee-sector'),

]