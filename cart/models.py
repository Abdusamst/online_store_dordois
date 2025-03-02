from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from store.models import Item, ItemAttributeValue

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Корзина',
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания',)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    @property
    def total_price(self):
        total_price = sum(item.total_price for item in self.items.all())
        return total_price

    def __str__(self):
        return f"Cart {self.id} for {self.user.username}"

    def clear(self):
        self.items.all().delete()


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Корзина',
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        verbose_name='Товар',
    )
    quantity = models.PositiveIntegerField(
        default=1, verbose_name='Количество',)
    attribute_values = models.ManyToManyField(
        ItemAttributeValue,
        blank=True,  # Allows for items with no attributes
        related_name='cart_items'
    )

    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'

    @property
    def total_price(self):
        base_price = self.item.price * self.quantity
        price_modifier = sum(
            attr.attribute_value.price_modifier or 0 
            for attr in self.attribute_values.all() 
            if attr.attribute_value  # Only include if attribute_value exists
        )
        return base_price + price_modifier

    def __str__(self):
        return f"{self.quantity} x {self.item.title}"