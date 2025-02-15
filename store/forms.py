from django import forms
from .models import Seller
from django import forms
from .models import Item
from .models import Item, ItemTag
from django import forms
from .models import Advertisement

class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ['image', 'link', 'position']

class ItemForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=ItemTag.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # Можно заменить на forms.SelectMultiple для списка
        required=True,
        label="Категории"
    )

    class Meta:
        model = Item
        fields = ['title', 'description', 'price', 'old_price', 'image', 'is_available', 'tags']


class SellerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = [
            'phone_number', 'whatsapp', 'store_type', 'stock_status', 
            'store_address', 'store_name', 'store_logo', 'seller_name', 
            'wants_to_sell_on_wildberries', 'wants_to_sell_on_ozon', 
            'has_store_on_wildberries', 'has_store_on_ozon'
        ]

    phone_number = forms.CharField(label='Номер телефона')
    whatsapp = forms.CharField(label='WhatsApp')
    STORE_TYPE_CHOICES = [
        ('warehouse', 'Склад'),
        ('shop', 'Магазин'),
        ('online_shop', 'Интернет-магазин'),
    ]
    store_type = forms.ChoiceField(choices=STORE_TYPE_CHOICES, label='Тип магазина')
    STOCK_STATUS_CHOICES = [
        ('in_stock', 'В наличии'),
        ('out_of_stock', 'Нет в наличии'),
        ('partial_stock', 'Частично в наличии'),
    ]
    stock_status = forms.ChoiceField(choices=STOCK_STATUS_CHOICES, label='Статус наличия товара')
    store_address = forms.CharField(label='Адрес магазина или склада')
    store_name = forms.CharField(label='Название магазина')
    store_logo = forms.ImageField(label='Логотип магазина')
    seller_name = forms.CharField(label='Имя и фамилия продавца')
    wants_to_sell_on_wildberries = forms.BooleanField(label='Хотите продавать на Wildberries', required=False)
    wants_to_sell_on_ozon = forms.BooleanField(label='Хотите продавать на Ozon', required=False)
    has_store_on_wildberries = forms.BooleanField(label='Есть магазин на Wildberries', required=False)
    has_store_on_ozon = forms.BooleanField(label='Есть магазин на Ozon', required=False)

from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text', 'user', 'images']
