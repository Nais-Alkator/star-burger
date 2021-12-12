from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views


from foodcartapp.models import Product, Restaurant, Order, OrderItem, RestaurantMenuItem
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


def select_suitable_restaurants_for_order(orders):
    restaurants = Restaurant.objects.all()
    orders = Order.objects.all()
    suitable_restaurants = []
    for restaurant in restaurants:
        for order in orders:
            restaurant_items = RestaurantMenuItem.objects.filter(restaurant=restaurant)
            products_of_restaurant = [restaurant_item.product for restaurant_item in restaurant_items]
            order_items = OrderItem.objects.filter(client=order)
            products_of_order = [order_item.product for order_item in order_items]
            for product in products_of_order:
                if product in products_of_restaurant:
                    suitable_restaurants.append(restaurant)
    suitable_restaurants = list(set(suitable_restaurants))
    return suitable_restaurants


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.all()
    orders_info = []
    for order in orders:
        order_items = OrderItem.objects.filter(client=order)
        price_of_order = order_items.aggregate(sum_of_order=Sum("price_product"))
        order_info = {"id": order.id, "firstname": order.firstname, "lastname": order.lastname, "phonenumber": order.phonenumber, "address": order.address,
                      "price_of_order": price_of_order["sum_of_order"], 
                      "status_of_order": order.get_status_of_order_display(), "payment_method": order.get_payment_method_display(), "comment": order.comment}
        orders_info.append(order_info)
    suitable_restaurants = select_suitable_restaurants_for_order(orders)
    orders_info = {"orders_info": orders_info, "suitable_restaurants": suitable_restaurants}
    return render(request, template_name='order_items.html', context=orders_info)
    