from django.http import JsonResponse
from django.templatetags.static import static
from .models import Product, Order, OrderItem, Restaurant, RestaurantMenuItem
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import OrderItemSerializer, OrderSerializer
from rest_framework import status
from django.db import transaction


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
@transaction.atomic
def register_order(request):
    order_serializer = OrderSerializer(data=request.data)
    order_serializer.is_valid(raise_exception=True)
    validated_data = order_serializer.validated_data
    order = Order.objects.create(firstname=validated_data["firstname"], lastname=validated_data["lastname"],
                                 phonenumber=validated_data["phonenumber"], address=validated_data["address"])

    products = validated_data['products']
    order_items = [
        OrderItem(
            order=order, total_product_price=product['quantity'] * product['product'].price, **product)
        for product in products
    ]
    OrderItem.objects.bulk_create(order_items)
    serialized_order = OrderSerializer(order)
    return Response(serialized_order.data, status=status.HTTP_201_CREATED)
