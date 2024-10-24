from rest_framework import serializers
import re
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import Employee, EmployeeHistory


class EmployeeSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    email = serializers.EmailField()
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
        # Aqui, o validated_data deve conter os campos diretamente
        password = validated_data.pop('password')
        
        # Criando o usuário
        user = User.objects.create_user(
            username=validated_data.pop('username'),
            email=validated_data.pop('email'),
            password=password
        )

        # Criando o Employee associado ao User
        employee = Employee.objects.create(user=user, **validated_data)

        # Se você deseja criar um histórico, pode usar os dados do employee
        EmployeeHistory.objects.create(
            name=employee.name,
            contact=employee.contact,
            address=employee.address,
            role=employee.role
        )

        return employee





class EmployeeHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeHistory
        fields = "__all__"


