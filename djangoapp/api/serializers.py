# api/serializers.py

from rest_framework import serializers
from .models import Employee
from .models import Product, Stock, Sale, ActionHistory
import re
from .models import Cart, CartItem
from rest_framework import serializers
from .models import Employee
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import LoginActivity

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

        # Criando o usuário (User)
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=password  # Hash da senha ocorre aqui
        )

        # Criando o Employee associado ao User
        employee = Employee.objects.create(user=user, **validated_data)

        return employee







class ProductSerializer(serializers.ModelSerializer):
    description = serializers.CharField(required=False)

    class Meta:
        model = Product
        fields = "__all__"



class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_price = serializers.ReadOnlyField(source='product.price')

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity']



class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'created_at']

        

class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = "__all__"

class LoginactivitySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = LoginActivity 
        fields = "__all__"
        extra_kwargs = {'username': {'read_only': True}} 


class StockManagerSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Stock
        fields = ['product', 'quantity', 'acquisition_value', 'responsible_user'] 

    def create(self, validated_data):
        return Stock.objects.create(**validated_data)

    

class ActionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionHistory
        fields = '__all__'


