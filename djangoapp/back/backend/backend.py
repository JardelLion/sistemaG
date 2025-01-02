# api/backends.py

from django.contrib.auth.backends import BaseBackend
import people.models as api

class UsernameBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Busca o funcionário pelo username
            print(f"Tentando autenticar: {username}, {password}")  # Para depuração
            employee = api.Employee.objects.get(username=username)
            # Verifica a senha
            if employee.check_password(password):
                return employee
            else:
                print("Senha incorreta.")
        except api.Employee.DoesNotExist:
            print("Funcionário não encontrado.")
            return None

    def get_user(self, user_id):
        try:
            return api.Employee.objects.get(pk=user_id)
        except api.Employee.DoesNotExist:
            return None
