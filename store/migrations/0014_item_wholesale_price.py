# Generated by Django 4.2.17 on 2025-02-17 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0013_alter_itemattributevalue_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='wholesale_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Оптовая цена'),
        ),
    ]
