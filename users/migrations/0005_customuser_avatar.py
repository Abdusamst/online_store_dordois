# Generated by Django 4.2.17 on 2025-02-10 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_customuser_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='avatar',
            field=models.ImageField(default='images/user.png', upload_to='avater/'),
        ),
    ]
