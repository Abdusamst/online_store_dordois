from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager 
from taggit .models import GenericTaggedItemBase, TagBase
from django.utils.text import slugify
from django.conf import settings
from django.db.models import Avg

from django.db import models
from django.db import models

class AttributeValue(models.Model):
    attribute = models.ForeignKey('ItemAttribute', related_name='values', on_delete=models.CASCADE, verbose_name='Атрибут')
    value = models.CharField(max_length=255, verbose_name='Значение')

    class Meta:
        verbose_name = 'Значение атрибута'
        verbose_name_plural = 'Значения атрибутов'

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"

class ItemAttribute(models.Model):
    ATTRIBUTE_TYPE_CHOICES = [
        ('dropdown', 'Dropdown'),
        ('radio', 'Radio'),
        ('color', 'Color'),
        ('text', 'Text'),
        # Добавь другие типы, если необходимо
    ]

    name = models.CharField(max_length=255, verbose_name='Название атрибута')
    type = models.CharField(max_length=50, choices=ATTRIBUTE_TYPE_CHOICES, verbose_name='Тип атрибута')
    required = models.BooleanField(default=False, verbose_name='Обязательный атрибут')
    tags = models.ManyToManyField('ItemTag', related_name='attributes', verbose_name='Категории (теги)', blank=True)

    class Meta:
        verbose_name = 'Атрибут товара'
        verbose_name_plural = 'Атрибуты товаров'

    def __str__(self):
        return self.name



class ItemTag(TagBase):
    image = models.ImageField(
        upload_to='categories/',
        verbose_name='Изображение',
        blank=True
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

from django.db import models
from django.conf import settings

class Review(models.Model):
    item = models.ForeignKey('store.Item', on_delete=models.CASCADE, related_name='reviews', verbose_name='Товар')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    text = models.TextField(verbose_name='Отзыв', blank=False)
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)], verbose_name='Рейтинг (1-5)', blank=False)
    images = models.ImageField(upload_to='reviews/', null=True, blank=True, verbose_name='Изображения отзыва')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'Отзыв от {self.user.username} на {self.item.title}'


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    item = models.ForeignKey(
        'store.Item',
        on_delete=models.CASCADE,
        verbose_name='Товар',
    )

class TaggedItem(GenericTaggedItemBase):
    tag = models.ForeignKey(
        ItemTag,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name='Категория',
    )
    
    

from django.db import models

class Advertisement(models.Model):
    POSITION_CHOICES = [
        ('top', 'Верхняя реклама'),
        ('bottom', 'Нижняя реклама'),
    ]

    image = models.ImageField(upload_to='ads/')
    link = models.URLField()
    position = models.CharField(max_length=10, choices=POSITION_CHOICES)

    def __str__(self):
        return f"{self.position} - {self.link}"


class Poster(models.Model):
    image = models.ImageField(
        upload_to='posters/',
        verbose_name='Изображение',
        blank=True
    )

    def __str__(self):
        return f"Poster {self.id}"

    class Meta:
        verbose_name = "Постер"
        verbose_name_plural = "Постеры"

class Item(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название',)
    description = models.TextField(verbose_name='Описание',)
    slug = models.SlugField(
        unique=True,
        blank=True,
    )
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления',)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Новая цена',
    )
    old_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Старая цена',
        blank=True,
        null=True,
    )
    wholesale_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Оптовая цена',
        blank=True,
        null=True,
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='items/',
        blank=True,
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name='Доступно',
    )
    is_approved = models.BooleanField(default=False, verbose_name="Одобрено администратором")  # ✅ Добавлено поле
    
    tags = TaggableManager(through=TaggedItem, related_name="tagged_items", verbose_name='Категории',)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,default = 1 ,related_name='items', verbose_name='Продавец')
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:  # если slug еще не создан
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Item.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)

    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    
    class Meta:
        ordering = ['-price']
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

class ItemAttributeValue(models.Model):
    item = models.ForeignKey(Item, related_name='attribute_values', on_delete=models.CASCADE)
    attribute = models.ForeignKey(ItemAttribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Значение атрибута товара'
        verbose_name_plural = 'Значения атрибутов товаров'

    def __str__(self):
        return f"{self.item.title} - {self.attribute.name}: {self.value}"



from django.contrib.auth.models import User

class Seller(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller', verbose_name='Пользователь')
    phone_number = models.CharField(max_length=20, verbose_name='Номер телефона')
    whatsapp = models.CharField(max_length=20, verbose_name='WhatsApp')
    STORE_TYPE_CHOICES = [
        ('warehouse', 'Склад'),
        ('shop', 'Магазин'),
        ('online_shop', 'Интернет-магазин'),
    ]
    store_type = models.CharField(max_length=20, choices=STORE_TYPE_CHOICES, verbose_name='Тип магазина')
    STOCK_STATUS_CHOICES = [
        ('in_stock', 'В наличии'),
        ('out_of_stock', 'Нет в наличии'),
        ('partial_stock', 'Частично в наличии'),
    ]
    stock_status = models.CharField(max_length=20, choices=STOCK_STATUS_CHOICES, verbose_name='Статус наличия товара')
    store_address = models.CharField(max_length=255, verbose_name='Адрес магазина или склада')
    store_name = models.CharField(max_length=255, verbose_name='Название магазина')
    store_logo = models.ImageField(upload_to='store_logos/', verbose_name='Логотип магазина')
    seller_name = models.CharField(max_length=255, verbose_name='Имя и фамилия продавца')
    wants_to_sell_on_wildberries = models.BooleanField(default=False, verbose_name='Хотите продавать на Wildberries')
    wants_to_sell_on_ozon = models.BooleanField(default=False, verbose_name='Хотите продавать на Ozon')
    has_store_on_wildberries = models.BooleanField(default=False, verbose_name='Есть магазин на Wildberries')
    has_store_on_ozon = models.BooleanField(default=False, verbose_name='Есть магазин на Ozon')

    def __str__(self):
        return self.store_name

    class Meta:
        verbose_name = 'Продавец'
        verbose_name_plural = 'Продавцы'

