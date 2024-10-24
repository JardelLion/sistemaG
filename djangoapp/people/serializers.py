from rest_framework import serializers
import re
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import Employee, EmployeeHistory
class EmployeeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
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
        """Verifica se o email já existe."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("Este email já está em uso."))
        return value

    def validate_contact(self, value):
        """Verifica se o contato possui o formato correto."""
        if not re.match(r'^\d{9,15}$', value):
            raise serializers.ValidationError(_("O campo de contato deve conter apenas números e ter entre 9 a 15 dígitos."))
        return value

    def validate_username(self, value):
        """Verifica se o nome de usuário já existe."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("Este nome de usuário já está em uso."))
        return value

    def create(self, validated_data):
        # Extraindo os dados do User
        user_data = validated_data.pop('user')
        password = validated_data.pop('password')

        name = validated_data['name']
        contact = validated_data['contact']
        address = validated_data['address']
        role = validated_data['role']

        # Criando o usuário (User)
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=password  # Hash da senha ocorre aqui
        )

        # Criando o Employee associado ao User
        employee = Employee.objects.create(user=user, **validated_data)

        EmployeeHistory.objects.create(
            name=name,
            contact=contact,
            address=address,
            role=role
        )

        return employee






class EmployeeHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeHistory
        fields = "__all__"


