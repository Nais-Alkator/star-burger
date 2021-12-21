from django.db import models
from django.utils import timezone


class Address(models.Model):
    address = models.CharField(verbose_name="адрес", max_length=50, unique=True)
    longitude = models.DecimalField(verbose_name="долгота", max_digits=11, decimal_places=8)
    latitude = models.DecimalField(verbose_name="широта", max_digits=10, decimal_places=8)
    date_of_request = models.DateTimeField(verbose_name="дата запроса", null=True, default=timezone.now)

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'

    def __str__(self):
        return self.address

