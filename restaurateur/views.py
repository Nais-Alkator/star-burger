from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views


from foodcartapp.models import Product, Restaurant, Order, OrderMenuItem
from django.db.models import Count, Sum
from django.db.models import F

class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    first_order = Order.objects.first()
    first_order = OrderMenuItem.objects.filter(client=first_order)
    for item in first_order:
        item.price_per_product = item.product.price
        item.save()
    print(first_order)
    print(type(first_order))
    print(first_order.values())
    first_order = first_order.annotate(sum_per_item=F("quantity")*F("price_per_product"))
    print(first_order.values())
    first_order = first_order.aggregate(sum_of_order=Sum("sum_per_item"))
    print(first_order)


    #price_order = first_order.annotate(price_order=F("quantity")



    orders = Order.objects.all()
    orders_info = []
    for order in orders:
        order_items = OrderMenuItem.objects.filter(client=order)
        for order_item in order_items:
            order_item.price_per_product = order_item.product.price
            order_item.save()
        order_items = order_items.annotate(sum_per_item=F("quantity")*F("price_per_product"))
        price_of_order = order_items.aggregate(sum_of_order=Sum("sum_per_item"))
        print("Тип order_items  ", type(price_of_order))


        order_info = {"id": order.id, "firstname": order.firstname, "lastname": order.lastname, "phonenumber": order.phonenumber, "address": order.address,
                      "price_of_order": price_of_order["sum_of_order"]}
        orders_info.append(order_info)
    orders_info = {"orders_info": orders_info}
    return render(request, template_name='order_items.html', context=orders_info)
