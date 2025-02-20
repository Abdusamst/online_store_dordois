from django.contrib import admin
from .models import Item, ItemTag, Poster, Seller, Review, Advertisement, Attribute, AttributeValue, ItemAttributeValue

@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'link', 'position')  # Показываем ID, картинку, ссылку и позицию
    list_filter = ('position',)  # Фильтр по позиции (верхняя/нижняя)
    search_fields = ('link',)  # Поиск по ссылке

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'phone_number', 'whatsapp', 'stock_status', 'store_address', 'seller_name']

from django.contrib import admin
from .models import Item, ItemTag, Poster, Seller, Review, Advertisement, Attribute, AttributeValue, ItemAttributeValue

class ItemAttributeValueInline(admin.TabularInline):
    model = ItemAttributeValue
    extra = 1  # Количество дополнительных форм для добавления

class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_description', 'slug', 'price',
                    'old_price', 'is_available', 'tag_list',)
    search_fields = ('title', 'description', 'tags__name',)
    list_filter = ('is_available', 'tags',)
    inlines = [ItemAttributeValueInline]  # Используем inlines вместо filter_horizontal

    def short_description(self, obj):
        if len(obj.description) > 100:
            return obj.description[:100] + '...'
        else:   
            return obj.description

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

    short_description.short_description = 'Описание'
    tag_list.short_description = 'Список категорий'

# ... остальные классы админки остаются без изменений ...

# Регистрация моделей с классами админки
admin.site.register(Item, ItemAdmin)

class ItemTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'short_description', 'item_list',)

    def short_description(self, obj):
        if len(obj.description) > 100:
            return obj.description[:100] + '...'
        else:
            return obj.description

    def item_list(self, obj):
        return [Item.objects.get(
            pk=o.get('object_id')
        ) for o in obj.items.values()]

    short_description.short_description = 'Описание'
    item_list.short_description = 'Список товаров'

class PosterAdmin(admin.ModelAdmin):
    list_display = ('image',)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('item', 'user', 'rating', 'text', 'created_at')
    search_fields = ('user__username', 'item__title', 'text')
    list_filter = ('rating', 'created_at')

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    search_fields = ('name',)

@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value', 'price_modifier')
    list_filter = ('attribute',)
    search_fields = ('attribute__name', 'value')

@admin.register(ItemAttributeValue)
class ItemAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('item', 'attribute_value')
    search_fields = ('item__title', 'attribute_value__value')

# Регистрация моделей с классами админки
admin.site.register(ItemTag, ItemTagAdmin)
admin.site.register(Poster, PosterAdmin)
admin.site.register(Review, ReviewAdmin)


from django.contrib import admin
from .models import AttributeCategory

@admin.register(AttributeCategory)
class AttributeCategoryAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'tag')