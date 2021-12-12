# Generated by Django 3.2 on 2021-12-04 15:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0032_remove_order_restaurant'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='restaurant',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='order_restaurant', to='foodcartapp.restaurant', verbose_name='Обслуживающий ресторан'),
            preserve_default=False,
        ),
    ]
