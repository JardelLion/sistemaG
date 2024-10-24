from django.contrib import admin
from django.urls import path, include
from django.urls import path


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include("api.urls")),
    path('api/people/', include("people.urls")),

    # path('api/employee/<uuid:id>/sales/', v.SalesByEmployeeWithIdViewSet.as_view({'get': 'list'}), name='sales-by-employee'),

    # path('api/notifications/', v.employee_notifications, name='employee_notifications'),
    # path('api/notifications/<uuid:notification_id>/read/', v.mark_as_read, name='mark_as_read'),




    # path('stock/entry/', v.StockEntryView.as_view(), name='stock-entry'),
    # path('cart/', v.CartViewSet.as_view({'get': 'list'})),
    # path('cart/add/', v.CartViewSet.as_view({'post': 'add_to_cart'})),
    # path('cart/remove/<uuid:pk>/', v.CartViewSet.as_view({'delete': 'remove_from_cart'})),
    # path('cart/items/<uuid:employee_id>/', v.CartItemsView.as_view(), name='cart-items') ,
   
   
]

