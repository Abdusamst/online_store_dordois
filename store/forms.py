from django import forms
from .models import Seller, Item, ItemTag, Advertisement, Attribute, AttributeValue

class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ['image', 'link', 'position']

from django import forms
from .models import Seller, Item, ItemTag, Advertisement, Attribute, AttributeValue, AttributeCategory

class ItemForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=ItemTag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Категории"
    )

    class Meta:
        model = Item
        fields = ['title', 'description', 'price', 'old_price', 'wholesale_price', 'quantity', 'image','image1', 'image2', 'image3', 'image4', 'video','to_order','is_available', 'tags']

    def __init__(self, *args, **kwargs):
        super(ItemForm, self).__init__(*args, **kwargs)
        self.attribute_fields_added = False

    def add_attribute_fields(self, tags):
        if self.attribute_fields_added:
            return
        
        attributes = Attribute.objects.filter(attributecategory__tag__in=tags).distinct()
        for attribute in attributes:
            field_name = f'attribute_{attribute.id}'
            choices = [(value.id, value.value) for value in attribute.values.all()]
            self.fields[field_name] = forms.MultipleChoiceField(
                label=f"{attribute.name} (выберите или добавьте)",
                choices=choices + [(-1, "Добавить новое значение")],
                widget=forms.CheckboxSelectMultiple,
                required=False
            )
            # Поле для нового значения
            self.fields[f'new_value_{attribute.id}'] = forms.CharField(
                label=f"Новое значение для {attribute.name}",
                required=False
            )
            # Поле для количества и модификатора цены для каждого значения
            for value in attribute.values.all():
                self.fields[f'quantity_{value.id}'] = forms.IntegerField(
                    label=f"Количество для {value.value}",
                    min_value=0,
                    required=False
                )
                self.fields[f'price_modifier_{value.id}'] = forms.DecimalField(
                    label=f"Модификатор цены для {value.value}",
                    decimal_places=2,
                    max_digits=10,
                    required=False
                )
            # Поля для нового значения
            self.fields[f'image_{value.id}'] = forms.ImageField(
                    label=f"Изображение для {value.value}",
                    required=False
                )
            self.fields[f'quantity_new_{attribute.id}'] = forms.IntegerField(
                label=f"Количество нового значения для {attribute.name}",
                min_value=0,
                required=False
            )
            # В методе add_attribute_fields добавить валидацию
            self.fields[f'price_modifier_new_{attribute.id}'] = forms.DecimalField(
                label=f"Модификатор цены нового значения для {attribute.name}",
                decimal_places=2,
                max_digits=10,
                required=False,
                initial=0  # Установить значение по умолчанию
            )

        self.attribute_fields_added = True

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
        fields = ['rating', 'text', 'images']