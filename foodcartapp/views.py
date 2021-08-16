from django.http import JsonResponse
from django.templatetags.static import static
from .models import Product, Orders, OrdersMenuItem
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type


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
    order_info = request.data
    print(order_info)
    required_keys = ["products", "firstname", "lastname", "phonenumber", "address"]
    for required_key in required_keys:
      if required_key not in order_info:
        raise KeyError("products, firstname, lastname, phonenumber, address: Обязательное поле.")
    if order_info["products"] == str(order_info["products"]):
        raise TypeError("products: Ожидался list со значениями, но был получен 'str'.")
    elif ("products", "firstname", "lastname", "phonenumber", "address") in order_info == None:
        raise ValueError("products, firstname, lastname, phonenumber, address: Это поле не может быть пустым.")
    elif len(order_info["products"]) == 0:
        raise ValueError("products: Этот список не может быть пустым.")
    elif order_info["firstname"] == None:
        raise ValueError("firstname: Это поле не может быть пустым.")
    elif len(order_info["phonenumber"]) == 0:
        raise ValueError("phonenumber: Это поле не может быть пустым.")
    elif carrier._is_mobile(number_type(phonenumbers.parse(order_info["phonenumber"]))) == False:
        raise ValueError("phonenumber': Введен некорректный номер телефона.")
    elif order_info["firstname"] != str(order_info["firstname"]):
        raise TypeError("firstname: Not a valid string.")
    order = Orders.objects.create(first_name=order_info["firstname"], last_name=order_info["lastname"], phone_number=order_info["phonenumber"], address=order_info["address"])
    for product in order_info["products"]:
        OrdersMenuItem.objects.create(client=order, product_id=product["product"], product_quantity=product["quantity"])
    return Response(order_info)
