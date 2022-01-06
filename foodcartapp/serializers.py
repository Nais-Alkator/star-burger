from django.http import JsonResponse
from django.templatetags.static import static
from .models import Product, Order, OrderItem
from rest_framework.serializers import ModelSerializer



class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["quantity", "product"]
        

class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(many=True, allow_empty=False, write_only=True)
    class Meta:
        model = Order
        fields = ["id", "firstname", "lastname", "phonenumber", "address", "products"]
        