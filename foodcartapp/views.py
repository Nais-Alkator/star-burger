from django.http import JsonResponse
from django.templatetags.static import static
from .models import Product, Order, OrderItem
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.serializers import Serializer
from rest_framework.serializers import ModelSerializer
from .serializers import OrderItemSerializer, OrderSerializer
from rest_framework import status


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()
    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    order_serializer = OrderSerializer(data=request.data)
    print("Успешно 1")
    order_serializer.is_valid(raise_exception=True)
    print("Успешно 2")
    order = Order.objects.create(firstname=order_serializer.validated_data["firstname"], lastname=order_serializer.validated_data["lastname"], 
        phonenumber=order_serializer.validated_data["phonenumber"], address=order_serializer.validated_data["address"])
    print("Успешно 3")
    products = [(Product.objects.get(id=product['product']), product['quantity']) for product in request.data['products']]
    print("Успешно 4")
    for product, quantity in products:
        OrderItem.objects.create(
            client=order,
            product=product,
            quantity=quantity,
            price_product=product.price * quantity
        )
        print("Успешно 5")
    order = OrderSerializer(order)
    print("Успешно 6")
    return Response(order.data, status=status.HTTP_201_CREATED)