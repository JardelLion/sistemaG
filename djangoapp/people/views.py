from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets
from .models import Employee, EmployeeHistory
from .serializers import EmployeeSerializer, EmployeeHistorySerializer
from .serializers import LoginactivitySerializer
from .models import LoginActivity

from rest_framework.response import Response

from rest_framework import viewsets, status
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    
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
                'username': employee['username'] if is_admin else None,
                'role': employee['role'],
                'stock_reference': employee['stock_reference']
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

# Token Authentication
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Tente obter o token de autenticação
        response = super().post(request, *args, **kwargs)

        # Verifique se o usuário foi autenticado
        user = authenticate(username=request.data.get('username'), password=request.data.get('password'))

        if user:
            LoginActivity.objects.create(
                user=user,
                
                status='success',
                ip_address=request.META.get("REMOTE_ADDR")

            )
            try:
                # Tente obter o funcionário associado ao usuário
                employee = Employee.objects.get(user=user)

                # Adicione os dados do funcionário à resposta
                response.data['employee'] = {
                    'id': employee.id,
                    'role': employee.role
                }
                response.data['error'] = None  # Remova qualquer mensagem de erro anterior
            except Employee.DoesNotExist:
                response.data['employee'] = None
                response.data['error'] = "Dados do funcionário não encontrados."
                response.status_code = status.HTTP_404_NOT_FOUND  # Alterado para 404, se preferir

        else:
            LoginActivity.objects.create(
                user=None,
                status='failure',
                id_address=request.META.get("REMOTE_ADDR")
            )
            response.data['employee'] = None
            response.data['error'] = "Credenciais inválidas."
            response.status_code = status.HTTP_401_UNAUTHORIZED

        return response



class LoginActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LoginActivity.objects.all()
    serializer_class = LoginactivitySerializer