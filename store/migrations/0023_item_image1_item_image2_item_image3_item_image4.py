# Generated by Django 4.2.17 on 2025-03-01 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0022_alter_seller_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='image1',
            field=models.ImageField(blank=True, null=True, upload_to='items/'),
        ),
        migrations.AddField(
            model_name='item',
            name='image2',
            field=models.ImageField(blank=True, null=True, upload_to='items/'),
        ),
        migrations.AddField(
            model_name='item',
            name='image3',
            field=models.ImageField(blank=True, null=True, upload_to='items/'),
        ),
        migrations.AddField(
            model_name='item',
            name='image4',
            field=models.ImageField(blank=True, null=True, upload_to='items/'),
        ),
    ]
