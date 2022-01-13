from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from foodcartapp.models import Product, Restaurant, Order, OrderItem, RestaurantMenuItem
import requests
from geopy.distance import lonlat, distance
import os
from address_and_places.models import Address
from django.conf import settings
from itertools import groupby

YANDEX_GEOCODER_API_TOKEN = settings.YANDEX_GEOCODER_API_TOKEN


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
        orderer_availability = [availability[restaurant.id]
                                for restaurant in restaurants]

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


def create_geodata_of_place(place):
    coordinates = fetch_coordinates(YANDEX_GEOCODER_API_TOKEN, place)
    address = Address.objects.get_or_create(
        address=place, longitude=coordinates[0], latitude=coordinates[1])
    return address


def select_suitable_restaurants_for_order(orders):
    restaurants = Restaurant.objects.all()
    orders = Order.objects.all()
    suitable_restaurants = []
    for restaurant in restaurants:
        for order in orders:
            restaurant_items = RestaurantMenuItem.objects.filter(
                restaurant=restaurant).select_related("product")
            products_of_restaurant = [
                restaurant_item.product for restaurant_item in restaurant_items]
            order_items = OrderItem.objects.filter(
                order=order).select_related("product")
            products_of_order = [
                order_item.product for order_item in order_items]
            for product in products_of_order:
                if product in products_of_restaurant:
                    suitable_restaurants.append(restaurant)
    suitable_restaurants = list(set(suitable_restaurants))
    return suitable_restaurants


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json(
    )['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    addresses = [address.address for address in Address.objects.all()]
    orders = Order.objects.all()
    orders_info = []
    suitable_restaurants = select_suitable_restaurants_for_order(orders)
    distances_to_suitable_restaurants = []
    for order in orders:
        restaurants = []
        if order.address not in addresses:
            order_address = create_geodata_of_place(order.address)
        elif order.address in addresses:
            order_address = Address.objects.get(address=order.address)
        for suitable_restaurant in suitable_restaurants:
            restaurant_address = create_geodata_of_place(
                suitable_restaurant.address)
            coordinates_of_restaurant = (
                suitable_restaurant.longitude, suitable_restaurant.latitude)
            distance_to_suitable_restaurant = distance(
                coordinates_of_restaurant, (order_address.longitude, order_address.latitude))
            distances_to_suitable_restaurants.append(
                distance_to_suitable_restaurant)
            restaurant = {"suitable_restaurant": suitable_restaurant,
                          "distance_to_suitable_restaurant": distance_to_suitable_restaurant}
            restaurants.append(restaurant)
        order_items = OrderItem.objects.filter(order=order)
        price_of_order = order_items.aggregate_price_order()
        restaurants = sorted(restaurants, key=lambda k: k['distance_to_suitable_restaurant'])
        order_info = {"id": order.id, "firstname": order.firstname, "lastname": order.lastname, "phonenumber": order.phonenumber, "address": order.address,
                      "price_of_order": price_of_order["sum_of_order"],
                      "status": order.get_status_display(), "payment_method": order.get_payment_method_display(), "comment": order.comment, "restaurants": restaurants}
        orders_info.append(order_info)
    orders_info = {"orders_info": orders_info}
    return render(request, template_name='order_items.html', context=orders_info)
