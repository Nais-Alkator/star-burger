# Generated by Django 3.2 on 2021-12-21 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('address_and_places', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='address',
            options={'verbose_name': 'Адрес', 'verbose_name_plural': 'Адреса'},
        ),
        migrations.AlterField(
            model_name='address',
            name='address',
            field=models.CharField(max_length=50, unique=True, verbose_name='адрес'),
        ),
    ]
