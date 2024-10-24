# people/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, EmployeeHistoryViewSet

# Cria uma instância do DefaultRouter
router = DefaultRouter()
# Registra os ViewSets no router
router.register(r'employee-history', EmployeeHistoryViewSet)
router.register(r'employee', EmployeeViewSet)

# Inclui as URLs do router
urlpatterns = [
    path('', include(router.urls)),  # Inclui as URLs registradas pelo router
]
