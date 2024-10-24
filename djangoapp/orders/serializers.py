from rest_framework import serializers
from .models import Sale, Stock, Cart, CartItem, Product

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


class StockManagerSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Stock
        fields = ['product', 'quantity', 'acquisition_value', 'responsible_user', 'available'] 

    def create(self, validated_data):
        return Stock.objects.create(**validated_data)

    

from .models import Stock

class StockManagerSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Stock
        fields = ['product', 'quantity', 'acquisition_value', 'responsible_user', 'available'] 

    def create(self, validated_data):
        return Stock.objects.create(**validated_data)

    

class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = "__all__"