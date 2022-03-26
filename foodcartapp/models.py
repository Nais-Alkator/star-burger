from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from django.db.models import Sum


class RestaurantQuerySet(models.QuerySet):
    def get_products_of_restaurants(self):
        restaurants = self.prefetch_related("menu_items")
        products_of_restaurants = []
        for restaurant in restaurants:
            products_of_restaurant = {'restaurant': restaurant, "products_ids": [restaurant.product_id for restaurant in restaurant.menu_items.all()]}
            products_of_restaurants.append(products_of_restaurant)
        return products_of_restaurants


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    longitude = models.DecimalField(
        verbose_name="долгота",
        max_digits=11,
        decimal_places=8)
    latitude = models.DecimalField(
        verbose_name="широта",
        max_digits=10,
        decimal_places=8)
    objects = RestaurantQuerySet.as_manager()

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def annotate_price(self):
        price = self.annotate(price=Sum("items__total_product_price"))
        return price

    def select_suitable_restaurants_for_orders(self, products_of_restaurants):
        suitable_restaurants_for_orders = []
        for order in self:
            suitable_restaurants = []
            order_items = order.items.all()
            products_of_order = [order_item.product_id for order_item in order_items]
            for products_of_restaurant in products_of_restaurants:
                if all(product in products_of_restaurant["products_ids"]
                       for product in products_of_order):
                    suitable_restaurants.append(products_of_restaurant["restaurant"])
            suitable_restaurants = {"order_id": order.id, "suitable_restaurants": suitable_restaurants}
            suitable_restaurants_for_order.append(suitable_restaurants)
        return suitable_restaurants_for_orders


class Order(models.Model):
    STATUS_CHOICES = [("PR", "Processed"), ("UNPR", "Unprocessed")]
    PAYMENT_METHOD_CHOICES = [
        ("cash", "Cash"), ("card", "Card"), ("ns", "not specified")]

    firstname = models.CharField(verbose_name="Имя", max_length=50)
    lastname = models.CharField(verbose_name="Фамилия", max_length=50)
    phonenumber = PhoneNumberField(
        verbose_name="Номер телефона", db_index=True)
    address = models.CharField(verbose_name="Адрес", max_length=100)
    status = models.CharField(
        verbose_name="Статус заказа",
        max_length=4,
        choices=STATUS_CHOICES,
        default="UNPR",
        db_index=True)
    comment = models.TextField(verbose_name="Комментарий к заказу", blank=True)
    registrated_at = models.DateTimeField(
        verbose_name="Зарегистрирован в",
        default=timezone.now,
        db_index=True)
    called_at = models.DateTimeField(
        verbose_name="Позвонили в",
        blank=True,
        null=True,
        db_index=True)
    delivered_at = models.DateTimeField(
        verbose_name="Доставлен в",
        blank=True,
        null=True,
        db_index=True)
    payment_method = models.CharField(
        verbose_name="Способ оплаты",
        max_length=15,
        choices=PAYMENT_METHOD_CHOICES,
        default="ns",
        db_index=True)
    restaurant = models.ForeignKey(
        Restaurant,
        verbose_name="Обслуживающий ресторан",
        related_name="orders",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        )
    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name="Заказ",
        related_name="items",
        on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product,
        verbose_name="Продукт",
        related_name="order_items",
        on_delete=models.CASCADE)
    quantity = models.IntegerField(
        verbose_name="Количество товара", validators=[
            MinValueValidator(1)])
    total_product_price = models.DecimalField(
        verbose_name="Цена товара c учетом количества",
        max_digits=7,
        decimal_places=2,
        validators=[
            MinValueValidator(0.0)])

    class Meta:
        verbose_name = "Элементы заказа"
        verbose_name_plural = "Элемент заказа"

    def __str__(self):
        return f"{self.order}"
