
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from store.models import Item
from .models import Cart, CartItem
from store.utils import generate_whatsapp_message
from store.models import ItemTag
from django.contrib import messages

@login_required
def cart(request):
    """
    Представление для вывода всех объектов товаров корзины и самой корзины.
    """
    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        cart = Cart.objects.create(user=request.user)

    cart_items = CartItem.objects.filter(cart=cart).prefetch_related('attribute_values')

    if request.method == 'POST':
        whatsapp_url = generate_whatsapp_message(cart_items)
        return redirect(whatsapp_url)
    page_obj_2 = ItemTag.objects.all()
    tags = ItemTag.objects.all().order_by('name')

    for tag in tags:
        tag.description = _(tag.description)

    context = {
        'page_obj_2': tags,
        'cart_items': cart_items,
        'cart': cart,
    }    

    return render(request, 'cart/cart.html', context)


from store.models import AttributeValue


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from store.models import Item, AttributeValue, ItemAttributeValue
from .models import Cart, CartItem

# cart/views.py
@login_required
def add_to_cart(request, item_slug):
    item = get_object_or_404(Item, slug=item_slug)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    # Проверяем, оптовая покупка или обычная
    is_wholesale = 'wholesale' in request.POST
    quantity = 10 if is_wholesale else int(request.POST.get('quantity', 1))  # Используем POST для一致性

    if quantity > item.quantity:
        messages.error(request, f'Невозможно добавить больше {item.quantity} {item.title} в корзину.')
        return redirect('store:item_details', item_slug=item.slug)

    # Собираем выбранные атрибуты из POST-запроса
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
        # Если нашли совпадение, устанавливаем количество для опта или прибавляем для обычной покупки
        matching_cart_item.quantity = quantity if is_wholesale else matching_cart_item.quantity + quantity
        if matching_cart_item.quantity > item.quantity:
            matching_cart_item.quantity = item.quantity
        matching_cart_item.save()
    else:
        # Создаем новый CartItem
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

    messages.success(request, f'{item.title} добавлен в корзину{" оптом" if is_wholesale else ""}!')
    return redirect('cart:cart')

@login_required
def delete_cart_item(request, item_slug):
    """
    Представление для удаления объекта товара в корзине.
    """
    cart_item = CartItem.objects.get(
        cart=Cart.objects.get(user=request.user),
        item=get_object_or_404(Item, slug=item_slug)
    )
    cart_item.delete()
    return redirect('cart:cart')


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from store.models import ItemAttributeValue

@login_required
def update_cart_item(request):
    if request.method == 'POST':
        cart_item_id = request.POST.get('cart_item_id')
        new_quantity = int(request.POST.get('new_quantity'))
        cart_id = int(request.POST.get('cart_id'))

        cart = get_object_or_404(Cart, pk=cart_id)
        cart_item = get_object_or_404(CartItem, id=cart_item_id)
        
        if 'attributes' in request.POST:
            # Clear existing attributes
            cart_item.attribute_values.clear()
            # Add new attributes
            for attr_id in request.POST.getlist('attributes'):
                attribute_value = get_object_or_404(ItemAttributeValue, id=attr_id)
                cart_item.attribute_values.add(attribute_value)

        cart_item.quantity = new_quantity
        cart_item.save()

        new_total_price = cart_item.total_price
        cart_total_price = sum(item.total_price for item in cart.items.all())

        return JsonResponse({
            'success': True,
            'cart_item_id': cart_item.id,
            'cart_item_quantity': cart_item.quantity,
            'cart_item_total_price': new_total_price,
            'cart_total_price': cart_total_price
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)