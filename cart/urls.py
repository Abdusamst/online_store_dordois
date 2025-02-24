from django.urls import path
from . import views
from .views import add_to_cart, cart, delete_cart_item, update_cart_item

app_name = 'cart'

urlpatterns = [
    path('', cart, name='cart'),
    path('add/<slug:item_slug>/', add_to_cart, name='add_to_cart'),
    path('cart/delete/<int:cart_item_id>/', views.delete_cart_item, name='delete_cart_item'),
    path('update_cart_item/', update_cart_item, name='update_cart_item'),
]
