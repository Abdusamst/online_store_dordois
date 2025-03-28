# Generated by Django 4.2.17 on 2025-03-13 09:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0023_item_image1_item_image2_item_image3_item_image4'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='itemattributevalue',
            options={},
        ),
        migrations.AddField(
            model_name='attributevalue',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='attributes/', verbose_name='Изображение'),
        ),
        migrations.AlterField(
            model_name='itemattributevalue',
            name='attribute_value',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.attributevalue'),
        ),
        migrations.AlterField(
            model_name='itemattributevalue',
            name='quantity',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterUniqueTogether(
            name='itemattributevalue',
            unique_together={('item', 'attribute_value')},
        ),
    ]
