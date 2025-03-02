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
from django.http import JsonResponse
from checkout.models import Order
from .models import Item, ItemTag, Attribute, AttributeValue, ItemAttributeValue
from .forms import ItemForm

def item_details(request, item_slug):
    item = get_object_or_404(Item, slug=item_slug)
    tags = ItemTag.objects.all().order_by('name')
    is_favorite = False
    has_bought = False  
    reviews = item.reviews.all()
    average_rating = item.average_rating()
    user_has_reviewed = False  
    item_attributes = item.attribute_values.select_related('attribute_value__attribute')
    item_attr_values = {attr.attribute_value.id: attr for attr in item.attribute_values.all()}

    if request.user.is_authenticated:
        has_bought = Order.objects.filter(user=request.user, items__item=item, status='delivered').exists()
        is_favorite = Favorite.objects.filter(user=request.user, item=item).exists()
        user_has_reviewed = reviews.filter(user=request.user).exists()

    # Обработка кнопки "Купить оптом"
    if request.method == 'POST' and 'wholesale' in request.POST:
        if item.wholesale_price and item.quantity >= 10:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            quantity = 10  # Оптовая покупка фиксирует количество 10

            # Собираем выбранные атрибуты из POST-запроса (если они есть)
            selected_attributes = {}
            for key, value in request.POST.items():
                if key.startswith('attribute_'):
                    attribute_id = key.split('_')[1]
                    attribute_value_id = int(value)
                    selected_attributes[attribute_id] = attribute_value_id

            # Ищем существующий CartItem с таким же набором атрибутов
            cart_items = CartItem.objects.filter(cart=cart, item=item)
            matching_cart_item = None
            for cart_item in cart_items:
                cart_item_attrs = {str(attr.attribute_value.attribute.id): attr.attribute_value.id 
                                 for attr in cart_item.attribute_values.all()}
                if cart_item_attrs == selected_attributes:
                    matching_cart_item = cart_item
                    break

            if matching_cart_item:
                # Если товар с такими атрибутами уже есть, обновляем количество до 10
                matching_cart_item.quantity = min(quantity, item.quantity)  # Не больше, чем в наличии
                matching_cart_item.save()
            else:
                # Создаем новый CartItem с количеством 10
                cart_item = CartItem.objects.create(cart=cart, item=item, quantity=quantity)
                for attribute_id, attribute_value_id in selected_attributes.items():
                    attribute_value = AttributeValue.objects.get(id=attribute_value_id)
                    item_attr_value, _ = ItemAttributeValue.objects.get_or_create(
                        item=item,
                        attribute_value=attribute_value,
                        defaults={'quantity': item.quantity}
                    )
                    cart_item.attribute_values.add(item_attr_value)
                cart_item.save()

            messages.success(request, 'Товар добавлен в корзину оптом!')
            return redirect('cart:cart')
        else:
            messages.error(request, 'Оптовая покупка недоступна для этого товара.')

    similar_items = Item.objects.filter(
        Q(tags__in=item.tags.all()) | Q(title__icontains=item.title.split()[0]),
        is_approved=True 
    ).exclude(id=item.id).distinct()[:4]

    context = {
        'page_obj_2': tags,
        'item': item,
        'is_favorite': is_favorite,
        'similar_items': similar_items,
        'reviews': reviews,
        'has_bought': has_bought,
        'average_rating': average_rating,
        'user_has_reviewed': user_has_reviewed,
        'item_attributes': item_attributes,
        'item_attr_values': item_attr_values,
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
    return redirect('store:favorite_list')

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
            Q(tags__name__icontains=query),
            is_approved=True
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
from .models import ItemTag
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



from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import Item, ItemTag, ItemAttributeValue, AttributeValue, Attribute, AttributeCategory
from .forms import ItemForm

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        tag_ids = request.POST.getlist('tags')
        tags = ItemTag.objects.filter(id__in=tag_ids)
        form.add_attribute_fields(tags)

        if form.is_valid():
            from django.db import transaction
            with transaction.atomic():
                item = form.save(commit=False)
                item.seller = request.user
                total_quantity = 0
                has_attributes = False

                # Сохраняем товар с базовой ценой
                item.save()

                for key, field_values in form.cleaned_data.items():
                    if key.startswith('attribute_') and field_values:
                        has_attributes = True
                        attribute_id = key.split('_')[1]
                        attribute = Attribute.objects.get(id=attribute_id)
                        new_value = form.cleaned_data.get(f'new_value_{attribute_id}')
                        new_quantity = form.cleaned_data.get(f'quantity_new_{attribute_id}', 0)
                        new_price_modifier_input = form.cleaned_data.get(f'price_modifier_new_{attribute_id}', 0)

                        # Новое значение атрибута
                        if new_value and new_quantity > 0:
                            price_modifier = new_price_modifier_input - item.price if new_price_modifier_input else 0
                            attribute_value, created = AttributeValue.objects.get_or_create(
                                attribute=attribute,
                                value=new_value,
                                defaults={'price_modifier': price_modifier}
                            )
                            if not created and new_price_modifier_input:
                                attribute_value.price_modifier = price_modifier
                                attribute_value.save()
                            ItemAttributeValue.objects.create(
                                item=item,
                                attribute_value=attribute_value,
                                quantity=new_quantity
                            )
                            total_quantity += new_quantity

                        # Существующие значения атрибутов
                        for value_id in field_values:
                            if str(value_id).isdigit():
                                value_id = int(value_id)
                                attribute_value = AttributeValue.objects.get(id=value_id)
                                quantity = form.cleaned_data.get(f'quantity_{value_id}', 0)
                                price_modifier_input = form.cleaned_data.get(f'price_modifier_{value_id}', 0)
                                if price_modifier_input:
                                    attribute_value.price_modifier = price_modifier_input - item.price
                                    attribute_value.save()
                                ItemAttributeValue.objects.update_or_create(
                                    item=item,
                                    attribute_value=attribute_value,
                                    defaults={'quantity': quantity}
                                )
                                total_quantity += quantity

                if not has_attributes:
                    total_quantity = form.cleaned_data.get('quantity', 0)
                item.quantity = total_quantity
                item.save()
                form.save_m2m()
            return redirect('store:thank_you')

    form = ItemForm()
    tags = ItemTag.objects.all()
    # ... остальной код для AJAX ...
                
    form = ItemForm()
    tags = ItemTag.objects.all()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'GET':
        tag_ids = request.GET.getlist('tags')
        
        tags = ItemTag.objects.filter(id__in=tag_ids)
        attribute_categories = AttributeCategory.objects.filter(tag__in=tags)
        
        # Use prefetch_related to avoid N+1 queries
        attributes = Attribute.objects.filter(
            attributecategory__tag__in=tags
        ).distinct().prefetch_related('values')
        
        dynamic_fields = []
        for attribute in attributes:
            values = attribute.values.all()
            field_data = {
                'attribute_id': attribute.id,
                'attribute_name': attribute.name,
                'attribute_type': attribute.type,
                'values': [{'id': value.id, 'value': value.value} for value in values]
            }
            dynamic_fields.append(field_data)
        
        return JsonResponse({'dynamic_fields': dynamic_fields})

    context = {
        'form': form,
        'tags': tags,
    }
    return render(request, 'store/add_item.html', context)
    
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



