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
from django.db.utils import IntegrityError
from urllib.error import HTTPError
import logging


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
    longitude, latitude = coordinates
    geodata_of_place = Address.objects.get_or_create(
        address=place, longitude=longitude, latitude=latitude)
    return geodata_of_place


def select_suitable_restaurants_for_order(restaurants, products_of_order):
    suitable_restaurants = []
    for products_of_restaurant in restaurants:
        if all(product in products_of_restaurant["products"]
               for product in products_of_order):
            suitable_restaurants.append(products_of_restaurant["restaurant"])
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
    orders = Order.objects.filter(status="UNPR")
    orders_info = []
    orders_addresses = list(orders.values_list("address", flat=True))
    geodata_of_orders = list(Address.objects.filter(
        address__in=orders_addresses).values_list("address", flat=True))

    for order_address in orders_addresses:
        if order_address not in geodata_of_orders:
            new__order_adress = create_geodata_of_place(order_address)

    restaurants = Restaurant.objects.all()
    products_of_restaurants = []
    for restaurant in restaurants:
        products_of_restaurant = {"restaurant": restaurant, "products": list(
            restaurant.menu_items.all().values_list("product", flat=True))}
        products_of_restaurants.append(products_of_restaurant)

    for order in orders:
        restaurants = []
        order_address = Address.objects.get(address=order.address)
        products_of_order = list(order.items.all().values_list("product", flat=True))
        suitable_restaurants = select_suitable_restaurants_for_order(
            products_of_restaurants, products_of_order)
        distances_to_suitable_restaurants = []
        for suitable_restaurant in suitable_restaurants:
            coordinates_of_restaurant = (
                suitable_restaurant.longitude, suitable_restaurant.latitude)
            distance_to_suitable_restaurant = distance(
                coordinates_of_restaurant, (order_address.longitude, order_address.latitude))
            distances_to_suitable_restaurants.append(
                distance_to_suitable_restaurant)
            restaurant = {"suitable_restaurant": suitable_restaurant,
                          "distance_to_suitable_restaurant": distance_to_suitable_restaurant}
            restaurants.append(restaurant)
        order_items = order.items.all()
        price_of_order = order_items.aggregate_price_order()
        restaurants = sorted(
            restaurants, key=lambda k: k['distance_to_suitable_restaurant'])
        order_info = {"id": order.id, "firstname": order.firstname, "lastname": order.lastname, "phonenumber": order.phonenumber, "address": order.address,
                      "price_of_order": round(price_of_order["sum_of_order"], 2),
                      "status": order.get_status_display(), "payment_method": order.get_payment_method_display(), "comment": order.comment, "restaurants": restaurants}
        orders_info.append(order_info)
    orders = {"orders_info": orders_info}
    return render(request, template_name='order_items.html', context=orders)
