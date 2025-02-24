
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
from django.shortcuts import get_object_or_404, redirect
from cart.models import Cart, CartItem
from store.models import Item, ItemAttributeValue
from django.db.models import Q

def add_to_cart(request, item_slug):
    item = get_object_or_404(Item, slug=item_slug)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Получаем выбранные атрибуты из POST-запроса
    selected_attributes = {}
    for key, value in request.POST.items():
        if key.startswith('attribute_'):
            attribute_id = key.replace('attribute_', '')
            selected_attributes[attribute_id] = value
    
    # Если атрибуты выбраны, ищем CartItem с таким же набором атрибутов
    if selected_attributes:
        # Получаем все CartItem для этого item в корзине
        cart_items = CartItem.objects.filter(cart=cart, item=item)
        
        # Ищем CartItem с таким же набором атрибутов
        for cart_item in cart_items:
            cart_item_attrs = {str(attr.attribute_value.attribute.id): attr.attribute_value.id for attr in cart_item.attribute_values.all()}
            if cart_item_attrs == selected_attributes:
                # Нашли совпадение, увеличиваем количество
                cart_item.quantity += 1
                cart_item.save()
                return redirect('cart:cart')
        
        # Если совпадений нет, создаем новый CartItem
        cart_item = CartItem.objects.create(cart=cart, item=item, quantity=1)
        for attr_id, value_id in selected_attributes.items():
            attr_value = get_object_or_404(ItemAttributeValue, item=item, attribute_value__id=value_id)
            cart_item.attribute_values.add(attr_value)
        cart_item.save()
    else:
        # Если атрибутов нет, добавляем или обновляем CartItem без атрибутов
        cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item)
        if not created:
            cart_item.quantity += 1
        cart_item.save()
    
    return redirect('cart:cart')

@login_required
def delete_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
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