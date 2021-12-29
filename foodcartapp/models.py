from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone


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

    longitude = models.DecimalField(verbose_name="долгота", max_digits=11, decimal_places=8)
    latitude = models.DecimalField(verbose_name="широта", max_digits=10, decimal_places=8)

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


class Order(models.Model):
    firstname = models.CharField(verbose_name="Имя", max_length=20)
    lastname = models.CharField(verbose_name="Фамилия", max_length=40)
    phonenumber = PhoneNumberField(verbose_name="Номер телефона", db_index=True)
    address = models.CharField(verbose_name="Адрес", max_length=100)
    STATUS_OF_ORDER_CHOICES = [("PR", "Processed"), ("UNPR", "Unprocessed")]
    status_of_order = models.CharField(verbose_name="Статус заказа", max_length=4, choices=STATUS_OF_ORDER_CHOICES, default="UNPR", db_index=True)
    comment = models.TextField(verbose_name="Комментарий к заказу", max_length=200, blank=True)
    registrated_at = models.DateTimeField(verbose_name="Зарегистрирован в", default=timezone.now, db_index=True)
    called_at = models.DateTimeField(verbose_name="Позвонили в", null=True, db_index=True)
    delivered_at = models.DateTimeField(verbose_name="Доставлен в", null=True, db_index=True)
    PAYMENT_METHOD_CHOICES = [("cash", "Cash"), ("card", "Card")]
    payment_method = models.CharField(verbose_name="Способ оплаты", max_length=15, choices=PAYMENT_METHOD_CHOICES, default="cash", db_index=True)
    restaurant = models.ForeignKey(Restaurant, verbose_name="Обслуживающий ресторан", null=True, related_name="order_restaurant", on_delete=models.CASCADE, default=1)
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class OrderItem(models.Model):
    client = models.ForeignKey(Order, verbose_name="Заказ", related_name="client", blank=True, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="Категория товара", related_name="order", null=True, blank=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(verbose_name="Количество товара", validators = [MinValueValidator(1)])
    price_product = models.DecimalField(verbose_name="Цена одного товара", max_digits=7, decimal_places=2, validators = [MinValueValidator(0.0)])

    class Meta:
        verbose_name = "Элементы заказа"
        verbose_name_plural = "Элемент заказа"

    def __str__(self):
        return f"{self.client.firstname}, {self.client.lastname}, {self.client.address}"