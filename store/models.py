from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager 
from taggit.models import GenericTaggedItemBase, TagBase
from django.utils.text import slugify
from django.conf import settings
from django.db.models import Avg

class Attribute(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название атрибута')
    type = models.CharField(max_length=20, choices=[
        ('dropdown', 'Выпадающий список'),
        ('checkbox', 'Чекбоксы'),
        ('text', 'Текстовое поле'),
        ('color', 'Выбор цвета')
    ], verbose_name='Тип атрибута')

    def __str__(self):
        return self.name
    





class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values', verbose_name='Атрибут')
    value = models.CharField(max_length=255, verbose_name='Значение')
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Модификатор цены')

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"

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
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

class AttributeCategory(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    tag = models.ForeignKey(ItemTag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('attribute', 'tag')

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
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(unique=True, blank=True)
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Новая цена')
    old_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Старая цена', blank=True, null=True)
    wholesale_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Оптовая цена', blank=True, null=True)
    image = models.ImageField(verbose_name='Изображение', upload_to='items/', blank=True)
    image1 = models.ImageField(upload_to='items/', blank=True, null=True)
    image2 = models.ImageField(upload_to='items/', blank=True, null=True)
    image3 = models.ImageField(upload_to='items/', blank=True, null=True)
    image4 = models.ImageField(upload_to='items/', blank=True, null=True)
    is_available = models.BooleanField(default=True, verbose_name='Доступно')
    is_approved = models.BooleanField(default=False, verbose_name="Одобрено администратором")
    quantity = models.PositiveIntegerField(default=0, verbose_name='Количество в наличии')
    video = models.FileField(upload_to='videos/', blank=True,null=True, verbose_name='Видео')
    to_order = models.BooleanField(default=False, verbose_name='Под заказа')
    tags = TaggableManager(through=TaggedItem, related_name="tagged_items", verbose_name='Категории')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1, related_name='items', verbose_name='Продавец')

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Item.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        if self.quantity <= 0:  
            self.is_available = False
        else:
            self.is_available = True
        super().save(*args, **kwargs)
        
    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    class Meta:
        ordering = ['-price']
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

# store/models.py
class ItemAttributeValue(models.Model):
    item = models.ForeignKey(Item, related_name='attribute_values', on_delete=models.CASCADE)
    attribute_value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('item', 'attribute_value')  # Добавляем это
    def __str__(self):
        return f"{self.item.title} - {self.attribute_value}"

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


