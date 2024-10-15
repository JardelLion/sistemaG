"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
   

)

import api.views as v




urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include("api.urls")),
    path('api/employee/<uuid:id>/sales/', v.SalesByEmployeeWithIdViewSet.as_view({'get': 'list'}), name='sales-by-employee'),




    path('stock/entry/', v.StockEntryView.as_view(), name='stock-entry'),
    path('cart/', v.CartViewSet.as_view({'get': 'list'})),
    path('cart/add/', v.CartViewSet.as_view({'post': 'add_to_cart'})),
    path('cart/remove/<uuid:pk>/', v.CartViewSet.as_view({'delete': 'remove_from_cart'})),
    path('cart/items/<uuid:employee_id>/', v.CartItemsView.as_view(), name='cart-items') ,
   
   
]

