# Generated by Django 4.2.17 on 2025-02-19 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0017_attribute_remove_itemattribute_tags_and_more'),
        ('checkout', '0007_remove_orderitem_attributes'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='attribute_values',
            field=models.ManyToManyField(blank=True, related_name='order_items', to='store.itemattributevalue', verbose_name='Атрибуты товара'),
        ),
    ]
