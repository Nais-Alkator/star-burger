# Generated by Django 3.2 on 2022-01-05 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0002_alter_order_restaurant'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('cash', 'Cash'), ('card', 'Card'), ('ns', 'not specified')], db_index=True, default='ns', max_length=15, verbose_name='Способ оплаты'),
        ),
    ]
