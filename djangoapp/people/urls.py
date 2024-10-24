# people/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, EmployeeHistoryViewSet, CustomTokenObtainPairView
from .views import LoginActivityViewSet

from people.views import employee_notifications, mark_as_read
# Cria uma instância do DefaultRouter
router = DefaultRouter()
# Registra os ViewSets no router
router.register(r'employee-history', EmployeeHistoryViewSet)
router.register(r'employee', EmployeeViewSet)
router.register(r'login-activities', LoginActivityViewSet, basename='log-activities')



# Inclui as URLs do router
urlpatterns = [
    path('', include(router.urls)),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('notifications/', employee_notifications, name='employee_notifications'),
    path('api/notifications/<uuid:notification_id>/read/', mark_as_read, name='mark_as_read'),

]
