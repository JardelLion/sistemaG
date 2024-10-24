from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets
from .models import Employee, EmployeeHistory
from .serializers import EmployeeSerializer, EmployeeHistorySerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    # permission_classes = [IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        current_employee = request.user.employee
        is_admin = current_employee.role == 'admin'
        
        filtered_employees = [
            {
                'id': employee['id'],
                'name': employee['name'],
                'email': employee['email'],
                'contact': employee['contact'],
                'address': employee['address'],
                'username': employee['username'] ,#if is_admin else None,
                'role': employee['role']
            }
            for employee in serializer.data #if employee['role'] == 'employee' 
        ]
        return Response(filtered_employees)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data

        # Captura dos dados antigos
        old_name = instance.name
        old_role = instance.role

        # Atualização dos dados do funcionário
        instance.name = data.get('name', instance.name)
        instance.role = data.get('role', instance.role)

        user = instance.user
        user.email = data.get('email', user.email)
        user.save()
        instance.save()

        # Criação de um novo histórico após a atualização
        if old_name != instance.name or old_role != instance.role:
            EmployeeHistory.objects.create(
                employee=instance,
                name=instance.name,
                contact=instance.contact,
                address=instance.address,
                role=instance.role,
                # você pode adicionar mais campos se necessário
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = instance.user

        instance.delete()
        user.delete()

        return Response({
            'message': 'Employee and related user deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

class EmployeeHistoryViewSet(viewsets.ModelViewSet):
    queryset = EmployeeHistory.objects.all()
    serializer_class = EmployeeHistorySerializer 
