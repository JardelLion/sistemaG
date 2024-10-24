from rest_framework.routers import DefaultRouter
from .views import EmployeeHistoryViewSet, EmployeeViewSet


route = DefaultRouter()
route.register(r'employee-history', EmployeeHistoryViewSet)
route.register(r'employee',EmployeeViewSet)

