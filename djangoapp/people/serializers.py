from rest_framework import serializers
import re
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import Employee, EmployeeHistory

class EmployeeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')  # Acessa o username do User
    email = serializers.EmailField(source='user.email')  # Acessa o email do User
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'name', 'username', 'email', 'contact', 'address', 'role', 'password']
        extra_kwargs = {
            'email': {'required': True},
            'contact': {'required': True},
            'password': {'write_only': True}
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("Este email já está em uso."))
        return value

    def validate_contact(self, value):
        if not re.match(r'^\d{9,15}$', value):
            raise serializers.ValidationError(_("O campo de contato deve conter apenas números e ter entre 9 a 15 dígitos."))
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("Este nome de usuário já está em uso."))
        return value
    
    def create(self, validated_data):
        # Tenta acessar os dados do User, se não existir, lança um erro
        user_data = validated_data.pop('user')  # Extrai o dicionário de dados do usuário
        password = validated_data.pop('password')  # Remove a senha do validated_data

        # Criando o usuário (User)
        user = User.objects.create_user(
            username=user_data['username'],  # Acesso ao username do User
            email=user_data['email'],  # Acesso ao email do User
            password=password  # A hash da senha ocorre aqui
        )

        # Criando o Employee associado ao User
        # Certifique-se de que 'user' não está em validated_data
        employee = Employee.objects.create(user=user, **validated_data)

        EmployeeHistory.objects.create(
            employee_id = employee.id,
            name=employee.name,  # Acessa o nome do Employee
            contact=employee.contact,  # Acessa o contato do Employee
            address=employee.address,  # Acessa o endereço do Employee
            role=employee.role  # Acessa o cargo do Employee
        )

        return employee

class EmployeeHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeHistory
        fields = "__all__"