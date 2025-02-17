from django.shortcuts import render
from .models import Item, ItemTag, Poster, Favorite, Advertisement
from .paginator import paginator
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Coalesce
from django.db.models import Count, FloatField, Avg

def store(request):
    items = Item.objects.filter(is_available=True, is_approved=True).annotate(
        order_count=Count('orderitem'),
        favorite_count=Count('favorite'),
        avg_rating=Coalesce(Avg('reviews__rating'), 0.0, output_field=FloatField())
    ).order_by('-order_count', '-favorite_count', '-avg_rating')
    top_ads = Advertisement.objects.filter(position='top')  # Должны быть 4
    bottom_ads = Advertisement.objects.filter(position='bottom')  # Должны быть 4
    tags = ItemTag.objects.all().order_by('name')
    posters = Poster.objects.all()
    favorites = Favorite.objects.filter(user=request.user).values_list('item_id', flat=True) if request.user.is_authenticated else []
    context = {
        'items': items,
        'page_obj_2': tags,
        'range': [*range(1, 7)],
        'posters': posters,
        'favorites': favorites,
        'top_ads': top_ads,   # Верхняя реклама
        'bottom_ads': bottom_ads,  # Нижняя реклама
    }
    return render(request, 'store/main_page.html', context)

from django.shortcuts import render, redirect
from .models import Advertisement
from .forms import AdvertisementForm

def add_advertisement(request):
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('store:home')  # После добавления вернемся на главную страницу
    else:
        form = AdvertisementForm()
    
    return render(request, 'store/add_advertisement.html', {'form': form})


@receiver(pre_save, sender=Item)
def create_slug(sender, instance, **kwargs):
    if not instance.slug:  # проверяем, есть ли уже slug
        instance.slug = slugify(instance.title)  # Используем title вместо name

def poster(request):
    posters = Poster.objects.all()
    context = {
        'posters': posters,
    }
    return render(request, 'store/poster.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from checkout.models import Order
from .models import Item, ItemTag, Review, Favorite

def item_details(request, item_slug):
    item = get_object_or_404(Item, slug=item_slug)
    tags = ItemTag.objects.all().order_by('name')
    is_favorite = False
    has_bought = False  # Установим False по умолчанию
    reviews = item.reviews.all()
    average_rating = item.average_rating()  # Добавил расчет среднего рейтинга
    user_has_reviewed = False  # Добавил проверку, оставил ли пользователь отзыв
    

    if request.user.is_authenticated:
        has_bought = Order.objects.filter(
            user=request.user,
            items__item=item,  # Убедись, что `items__item` соответствует реальной связи в модели
            status='delivered'  # Убедись, что статус точно такой же в БД
        ).exists()
        is_favorite = Favorite.objects.filter(user=request.user, item=item).exists()
        user_has_reviewed = reviews.filter(user=request.user).exists()

    similar_items = Item.objects.filter(
        Q(tags__in=item.tags.all()) |
        Q(title__icontains=item.title.split()[0])
    ).exclude(id=item.id).distinct()[:4]

    context = {
        'page_obj_2': tags,
        'item': item,
        'is_favorite': is_favorite,
        'similar_items': similar_items,
        'reviews': reviews,
        'has_bought': has_bought,
        'average_rating': average_rating,  # Передаем средний рейтинг в контекст
        'user_has_reviewed': user_has_reviewed,  # Передаем информацию о наличии отзыва
    }
    return render(request, 'store/item_details.html', context)

@login_required
def add_review(request, item_slug):
    item = get_object_or_404(Item, slug=item_slug)
    
    
    has_bought = Order.objects.filter(
        user=request.user, 
        items__item=item,
        status='delivered'
    ).exists()
    

    if not has_bought:
        messages.error(request, 'Вы можете оставить отзыв только после покупки товара.')
        return redirect('store:item_details', item_slug=item.slug)

    if request.method == 'POST':
        
        text = request.POST.get('text')
        rating = request.POST.get('rating')
        image = request.FILES.get('image')
        
        
        if not text or not rating:
            print("Missing required fields")  # Отладочная информация
            messages.error(request, 'Пожалуйста, заполните все обязательные поля.')
            return redirect('store:item_details', item_slug=item.slug)
        
        try:
            review = Review.objects.create(
                item=item,
                user=request.user,
                text=text,
                rating=rating,
                images=image
            )
            messages.success(request, 'Спасибо! Ваш отзыв успешно добавлен.')
        except Exception as e:
            messages.error(request, f'Произошла ошибка при сохранении отзыва: {str(e)}')
            
    return redirect('store:item_details', item_slug=item.slug)

from django.shortcuts import render, get_object_or_404
from .models import Item, Review

def all_reviews(request, item_slug):  # Используйте item_slug
    item = get_object_or_404(Item, slug=item_slug)
    reviews = Review.objects.filter(item=item)
    average_rating = item.average_rating()

    context = {
        'item': item,
        'reviews': reviews,
        'average_rating': average_rating,
    }
    return render(request, 'store/all_reviews.html', context)

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

@staff_member_required
def moderator_panel(request):
    return render(request, 'store/moderator_panel.html')

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import ItemTag, Item

def tag_details(request, slug):
    tag = get_object_or_404(ItemTag, slug=slug)
    items = Item.objects.filter(tags=tag, is_available=True, is_approved=True)  # Вместо tags__in=[tag]
    paginator = Paginator(items, 10)  # отобразить 10 товаров на странице

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    page_obj_2 = ItemTag.objects.all()
    tags = ItemTag.objects.all().order_by('name')

    context = {
        'tag': tag,
        'page_obj': page_obj,
        'tags': tags,
        'page_obj_2': tags,
    }

    return render(request, 'store/tag_details.html', context)


def tag_list(request):
    tags = ItemTag.objects.all()
    for tag in tags:
        tag.description = _(tag.description)
        tag.name = _(tag.name)
    page_obj_2 = ItemTag.objects.all()
    tags = ItemTag.objects.all().order_by('name')
    context = {
        'page_obj': paginator(request, tags, 6),                                                                                                        
        'tags': tags,
        'page_obj_2': tags,
    }
    return render(request, 'store/tag_list.html', context)



from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Favorite, Item

@login_required
def add_to_favorites(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    Favorite.objects.get_or_create(user=request.user, item=item)
    return redirect(reverse('store:item_details', kwargs={'item_slug': item.slug}))

@login_required
def remove_from_favorites(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    favorite = get_object_or_404(Favorite, user=request.user, item=item)
    favorite.delete()
    return redirect(reverse('store:item_details', kwargs={'item_slug': item.slug}))

@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user)
    page_obj_2 = ItemTag.objects.all()
    tags = ItemTag.objects.all().order_by('name')
    context = {
        'tags': tags,
        'page_obj_2': tags,
        'favorites': favorites
    }
    return render(request, 'store/favorite_list.html', context)




from django.http import JsonResponse

@login_required
def toggle_favorite(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, item=item)
    if not created:
        favorite.delete()
        action = 'removed'
    else:
        action = 'added'
    return JsonResponse({'action': action})

from django.db.models import Q
from django.shortcuts import render
from .models import Item, ItemTag

def search(request):
    query = request.GET.get('q')
    if query:
        results = Item.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    else:
        results = Item.objects.all()  # Показываем все товары, если запрос пуст
    page_obj_2 = ItemTag.objects.all()
    tags = ItemTag.objects.all().order_by('name')
    context = {
        'tags': tags,
        'page_obj_2': tags,
        'query': query,
        'results': results,
    }
    return render(request, 'store/search.html', context)


from .forms import SellerRegistrationForm

from django.shortcuts import render, redirect
from .forms import SellerRegistrationForm, ItemForm
from .models import Seller, Item

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SellerRegistrationForm
from .models import User, Seller, ItemTag
import urllib.parse

@login_required
def become_seller(request):
    tags = ItemTag.objects.all().order_by('name')
    page_obj_2 = tags  # Если `page_obj_2` требуется в шаблоне, просто присваиваем `tags`

    if request.user.is_seller:
        messages.info(request, 'Вы уже продавец.')
        return redirect('store:home')

    # Если пользователь не продавец, отправляем его в чат WhatsApp с менеджером
    whatsapp_number = "+996552840777"  # Замените на номер менеджера
    message = "Здравствуйте! Я хочу стать продавцом в вашем магазине."
    whatsapp_url = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(message)}"

    return redirect(whatsapp_url)

    return render(request, 'store/becomeseller.html', {'tags': tags, 'page_obj_2': page_obj_2})



from django.template.loader import render_to_string
from .models import Item, ItemTag, ItemAttributeValue, AttributeValue

@login_required
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        tag_ids = request.POST.getlist('tags')
        tags = ItemTag.objects.filter(id__in=tag_ids)
        form.add_attribute_fields(tags)

        if form.is_valid():
            item = form.save(commit=False)
            item.seller = request.user
            item.save()
            form.save_m2m()

            # Сохранение значений атрибутов
            for field_name, field_value in form.cleaned_data.items():
                if field_name.startswith('attribute_'):
                    attribute = form.fields[field_name].attribute
                    value = field_value

                    if attribute.type in ['dropdown', 'radio']:
                        attribute_value = AttributeValue.objects.get(id=value)
                        # Сохраняем связь между товаром и значением атрибута
                        ItemAttributeValue.objects.create(
                            item=item,
                            attribute=attribute,
                            value=attribute_value.value
                        )
                    else:
                        # Для текстовых или цветовых данных
                        ItemAttributeValue.objects.create(
                            item=item,
                            attribute=attribute,
                            value=value
                        )

            return redirect('store:thank_you')

    else:
        form = ItemForm()
        tags = ItemTag.objects.all()

    # AJAX для загрузки атрибутов при выборе категорий
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'GET':
        tag_ids = request.GET.getlist('tags')
        tags = ItemTag.objects.filter(id__in=tag_ids)

        form = ItemForm()
        form.add_attribute_fields(tags)

        # Возвращаем HTML для атрибутов
        attribute_fields_html = render_to_string(
            'store/attribute_fields.html',
            {'form': form},
            request=request
        )
        return JsonResponse({'html': attribute_fields_html})

    return render(request, 'store/add_item.html', {'form': form, 'tags': tags})




def thank_you(request):
    return render(request, 'store/thank_you.html')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Item, ItemTag
from checkout.models import OrderItem
from cart.models import CartItem

@login_required
def my_items(request):
    seller = request.user
    items = Item.objects.filter(seller=seller)

    context = {
        'items': items,
        'tags': ItemTag.objects.all().order_by('name'),
        'page_obj_2': ItemTag.objects.all(),
    }
    return render(request, 'store/my_items.html', context)


@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, seller=request.user)  # Используйте объект CustomUser вместо Seller
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('store:my_items')
    else:
        form = ItemForm(instance=item)

    page_obj_2 = ItemTag.objects.all()
    tags = ItemTag.objects.all().order_by('name')
    context = {
        'item': item,
        'form': form,
        'tags': tags,
        'page_obj_2': tags,
    }
    return render(request, 'store/edit_item.html', context)

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, seller=request.user)
    if request.method == 'POST':
        item.delete()
        return redirect('store:my_items')
    
    page_obj_2 = ItemTag.objects.all()
    tags = ItemTag.objects.all().order_by('name')
    context = {
        'item': item,
        'tags': tags,
        'page_obj_2': tags,
    }
    return render(request, 'store/delete_item.html', context)



def add_category_attributes(apps, schema_editor):
    ItemTag = apps.get_model('store', 'ItemTag')
    ItemAttribute = apps.get_model('store', 'ItemAttribute')
    AttributeValue = apps.get_model('store', 'AttributeValue')
    
    # 1. Бытовая техника
    appliances_tag = ItemTag.objects.get(name='Бытовая техника')
    
    # Атрибут "Бренд" для бытовой техники
    brand_attr, _ = ItemAttribute.objects.get_or_create(
        name='Бренд',
        type='dropdown',
        required=True
    )
    brand_attr.tags.add(appliances_tag)
    
    # Значения для брендов бытовой техники
    for brand in ['LG', 'Samsung', 'Bosch', 'Philips', 'Tefal', 'Electrolux', 'Siemens']:
        AttributeValue.objects.get_or_create(attribute=brand_attr, value=brand)
    
    # Атрибут "Тип техники" для бытовой техники
    appliance_type_attr, _ = ItemAttribute.objects.get_or_create(
        name='Тип техники',
        type='dropdown',
        required=True
    )
    appliance_type_attr.tags.add(appliances_tag)
    
    # Значения для типов техники
    for appliance_type in ['Холодильник', 'Стиральная машина', 'Микроволновка', 'Пылесос', 'Утюг', 'Чайник', 'Кофеварка']:
        AttributeValue.objects.get_or_create(attribute=appliance_type_attr, value=appliance_type)
    
    # Атрибут "Гарантия" для бытовой техники
    warranty_attr, _ = ItemAttribute.objects.get_or_create(
        name='Гарантия',
        type='dropdown',
        required=False
    )
    warranty_attr.tags.add(appliances_tag)
    
    # Значения для гарантии
    for warranty in ['6 месяцев', '12 месяцев', '24 месяца', '36 месяцев']:
        AttributeValue.objects.get_or_create(attribute=warranty_attr, value=warranty)
    
    # 2. Косметика
    cosmetics_tag = ItemTag.objects.get(name='Косметика')
    
    # Атрибут "Бренд" для косметики
    cosmetics_brand_attr, _ = ItemAttribute.objects.get_or_create(
        name='Бренд',
        type='dropdown',
        required=True
    )
    cosmetics_brand_attr.tags.add(cosmetics_tag)
    
    # Значения для брендов косметики
    for brand in ['L\'Oreal', 'Maybelline', 'MAC', 'Clinique', 'Estée Lauder', 'NYX', 'Nivea']:
        AttributeValue.objects.get_or_create(attribute=cosmetics_brand_attr, value=brand)
    
    # Атрибут "Тип продукта" для косметики
    cosmetics_type_attr, _ = ItemAttribute.objects.get_or_create(
        name='Тип продукта',
        type='dropdown',
        required=True
    )
    cosmetics_type_attr.tags.add(cosmetics_tag)
    
    # Значения для типов косметики
    for cosmetic_type in ['Тушь для ресниц', 'Помада', 'Тональный крем', 'Тени для век', 'Румяна', 'Пудра', 'Лак для ногтей']:
        AttributeValue.objects.get_or_create(attribute=cosmetics_type_attr, value=cosmetic_type)
    
    # Атрибут "Цвет" для косметики
    color_attr, _ = ItemAttribute.objects.get_or_create(
        name='Цвет',
        type='color',
        required=False
    )
    color_attr.tags.add(cosmetics_tag)
    
    # 3. Детские товары
    baby_tag = ItemTag.objects.get(name='Детские товары')
    
    # Атрибут "Возрастная группа" для детских товаров
    age_group_attr, _ = ItemAttribute.objects.get_or_create(
        name='Возрастная группа',
        type='dropdown',
        required=True
    )
    age_group_attr.tags.add(baby_tag)
    
    # Значения для возрастных групп
    for age_group in ['0-1 год', '1-3 года', '3-5 лет', '5-7 лет', '7-10 лет', '10-14 лет']:
        AttributeValue.objects.get_or_create(attribute=age_group_attr, value=age_group)
    
    # Атрибут "Тип товара" для детских товаров
    baby_product_type_attr, _ = ItemAttribute.objects.get_or_create(
        name='Тип товара',
        type='dropdown',
        required=True
    )
    baby_product_type_attr.tags.add(baby_tag)
    
    # Значения для типов детских товаров
    for product_type in ['Игрушки', 'Одежда', 'Коляски', 'Питание', 'Гигиена', 'Мебель', 'Развивающие игры']:
        AttributeValue.objects.get_or_create(attribute=baby_product_type_attr, value=product_type)
    
    # Атрибут "Материал" для детских товаров
    baby_material_attr, _ = ItemAttribute.objects.get_or_create(
        name='Материал',
        type='dropdown',
        required=False
    )
    baby_material_attr.tags.add(baby_tag)
    
    # Значения для материалов детских товаров
    for material in ['Пластик', 'Дерево', 'Хлопок', 'Плюш', 'Силикон', 'Металл']:
        AttributeValue.objects.get_or_create(attribute=baby_material_attr, value=material)
    
    # 4. Спорт товары
    sport_tag = ItemTag.objects.get(name='Спорт товары')
    
    # Атрибут "Вид спорта" для спортивных товаров
    sport_type_attr, _ = ItemAttribute.objects.get_or_create(
        name='Вид спорта',
        type='dropdown',
        required=True
    )
    sport_type_attr.tags.add(sport_tag)
    
    # Значения для видов спорта
    for sport_type in ['Футбол', 'Баскетбол', 'Теннис', 'Плавание', 'Фитнес', 'Йога', 'Бег', 'Велоспорт']:
        AttributeValue.objects.get_or_create(attribute=sport_type_attr, value=sport_type)
    
    # Атрибут "Размер" для спортивных товаров
    sport_size_attr, _ = ItemAttribute.objects.get_or_create(
        name='Размер',
        type='dropdown',
        required=False
    )
    sport_size_attr.tags.add(sport_tag)
    
    # Значения для размеров спортивных товаров
    for size in ['XS', 'S', 'M', 'L', 'XL', 'XXL']:
        AttributeValue.objects.get_or_create(attribute=sport_size_attr, value=size)
    
    # Атрибут "Бренд" для спортивных товаров
    sport_brand_attr, _ = ItemAttribute.objects.get_or_create(
        name='Бренд',
        type='dropdown',
        required=False
    )
    sport_brand_attr.tags.add(sport_tag)
    
    # Значения для брендов спортивных товаров
    for brand in ['Nike', 'Adidas', 'Puma', 'Reebok', 'Under Armour', 'Wilson', 'Speedo']:
        AttributeValue.objects.get_or_create(attribute=sport_brand_attr, value=brand)
    
    # 5. Одежда и обувь
    clothing_tag = ItemTag.objects.get(name='Одежда и обувь')
    
    # Атрибут "Размер одежды" для одежды
    clothing_size_attr, _ = ItemAttribute.objects.get_or_create(
        name='Размер одежды',
        type='dropdown',
        required=True
    )
    clothing_size_attr.tags.add(clothing_tag)
    
    # Значения для размеров одежды
    for size in ['XS', 'S', 'M', 'L', 'XL', 'XXL']:
        AttributeValue.objects.get_or_create(attribute=clothing_size_attr, value=size)
    
    # Атрибут "Размер обуви" для обуви
    shoe_size_attr, _ = ItemAttribute.objects.get_or_create(
        name='Размер обуви',
        type='dropdown',
        required=True
    )
    shoe_size_attr.tags.add(clothing_tag)
    
    # Значения для размеров обуви
    for size in range(35, 46):
        AttributeValue.objects.get_or_create(attribute=shoe_size_attr, value=str(size))
    
    # Атрибут "Материал" для одежды и обуви
    clothing_material_attr, _ = ItemAttribute.objects.get_or_create(
        name='Материал',
        type='dropdown',
        required=False
    )
    clothing_material_attr.tags.add(clothing_tag)
    
    # Значения для материалов одежды и обуви
    for material in ['Хлопок', 'Лен', 'Шерсть', 'Полиэстер', 'Кожа', 'Шелк', 'Деним']:
        AttributeValue.objects.get_or_create(attribute=clothing_material_attr, value=material)
    
    # Атрибут "Цвет" для одежды и обуви
    clothing_color_attr, _ = ItemAttribute.objects.get_or_create(
        name='Цвет',
        type='radio',
        required=True
    )
    clothing_color_attr.tags.add(clothing_tag)
    
    # Значения для цветов одежды и обуви
    for color in ['Черный', 'Белый', 'Красный', 'Синий', 'Зеленый', 'Желтый', 'Серый', 'Бежевый']:
        AttributeValue.objects.get_or_create(attribute=clothing_color_attr, value=color)
    
    # 6. Концтовары
    office_tag = ItemTag.objects.get(name='Концтовары')
    
    # Атрибут "Тип товара" для концтоваров
    office_type_attr, _ = ItemAttribute.objects.get_or_create(
        name='Тип товара',
        type='dropdown',
        required=True
    )
    office_type_attr.tags.add(office_tag)
    
    # Значения для типов концтоваров
    for office_type in ['Ручки', 'Карандаши', 'Блокноты', 'Бумага', 'Папки', 'Степлеры', 'Калькуляторы']:
        AttributeValue.objects.get_or_create(attribute=office_type_attr, value=office_type)
    
    # Атрибут "Цвет" для концтоваров
    office_color_attr, _ = ItemAttribute.objects.get_or_create(
        name='Цвет',
        type='dropdown',
        required=False
    )
    office_color_attr.tags.add(office_tag)
    
    # Значения для цветов концтоваров
    for color in ['Черный', 'Синий', 'Красный', 'Зеленый', 'Желтый', 'Белый', 'Ассорти']:
        AttributeValue.objects.get_or_create(attribute=office_color_attr, value=color)
    
    # Атрибут "Бренд" для концтоваров
    office_brand_attr, _ = ItemAttribute.objects.get_or_create(
        name='Бренд',
        type='dropdown',
        required=False
    )
    office_brand_attr.tags.add(office_tag)
    
    # Значения для брендов концтоваров
    for brand in ['Parker', 'Pilot', 'Erich Krause', 'BIC', 'Moleskine', 'Stabilo', 'Schneider']:
        AttributeValue.objects.get_or_create(attribute=office_brand_attr, value=brand)
    
    # 7. Скидки и бонусы - доп. атрибутов не требуется, так как это скорее маркетинговая категория
    # 8. Подарки
    gift_tag = ItemTag.objects.get(name='Подарки')
    
    # Атрибут "Повод" для подарков
    occasion_attr, _ = ItemAttribute.objects.get_or_create(
        name='Повод',
        type='dropdown',
        required=True
    )
    occasion_attr.tags.add(gift_tag)
    
    # Значения для поводов подарков
    for occasion in ['День рождения', 'Новый год', '8 марта', '23 февраля', 'Свадьба', 'Юбилей', 'Профессиональный праздник']:
        AttributeValue.objects.get_or_create(attribute=occasion_attr, value=occasion)
    
    # Атрибут "Для кого" для подарков
    recipient_attr, _ = ItemAttribute.objects.get_or_create(
        name='Для кого',
        type='dropdown',
        required=True
    )
    recipient_attr.tags.add(gift_tag)
    
    # Значения для получателей подарков
    for recipient in ['Для мужчин', 'Для женщин', 'Для детей', 'Для пар', 'Для коллег', 'Для руководителя']:
        AttributeValue.objects.get_or_create(attribute=recipient_attr, value=recipient)
    
    # Атрибут "Ценовая категория" для подарков
    price_category_attr, _ = ItemAttribute.objects.get_or_create(
        name='Ценовая категория',
        type='radio',
        required=False
    )
    price_category_attr.tags.add(gift_tag)
    
    # Значения для ценовых категорий подарков
    for price_category in ['Эконом (до 1000 руб)', 'Стандарт (1000-3000 руб)', 'Премиум (3000-10000 руб)', 'VIP (более 10000 руб)']:
        AttributeValue.objects.get_or_create(attribute=price_category_attr, value=price_category)