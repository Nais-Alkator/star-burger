from django.http import JsonResponse
from django.templatetags.static import static
from .models import Product, Order, OrderItem
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type
from rest_framework.serializers import ValidationError
from rest_framework.serializers import Serializer
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import ListField


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["quantity", "client", "product"]
        

class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(many=True, allow_empty=False, write_only=True)
    class Meta:
        model = Order
        fields = ["id", "firstname", "lastname", "phonenumber", "address", "products"]
        