from rest_framework import serializers
from .models import Sale, Stock, Cart, CartItem, Product, Notification
from rest_framework.exceptions import ValidationError

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ['stock_reference']  # Torna o campo somente leitura para evitar exigência no payload

    def create(self, validated_data):
        # Busca o estoque ativo
        active_stock_reference = StockReference.objects.filter(is_active=True).first()
        if not active_stock_reference:
            raise serializers.ValidationError({"stock_reference": "No active stock reference found."})
        
        # Associa o estoque ativo ao produto
        validated_data['stock_reference'] = active_stock_reference
        return super().create(validated_data)

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


class StockManagerSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Stock
        fields = ['product', 'quantity', 'responsible_user', 'available', 'stock_reference'] 

    def create(self, validated_data):
        return Stock.objects.create(**validated_data)


class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'employee', 'message', 'product_description', 'is_read', 'created_at']
        read_only_fields = ['id', 'employee', 'created_at']

from . models import StockReference
class StockReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockReference
        fields = '__all__'