import asyncio

import telegram
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from OnlineStore.settings import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
from checkout.models import Order
from .forms import CreationForm, FeedbackForm
from .models import Feedback
from store.models import ItemTag


@login_required
def user_orders(request):
    """
    Представление списка заказов пользователя.
    """
    orders = Order.objects.filter(user=request.user).prefetch_related('items__attribute_values')
    page_obj_2 = ItemTag.objects.all()
    tags = ItemTag.objects.all().order_by('name')
    context = {
        'orders': orders,
        'tags': tags,
        'page_obj_2': tags,
    }
    return render(request, 'users/user_orders.html', context)


@login_required
def profile(request):
    """
    Представление профиля пользователя.
    """
    page_obj_2 = ItemTag.objects.all()
    tags = ItemTag.objects.all().order_by('name')
    context = {
        'tags': tags,
        'page_obj_2': tags,
    }
    return render(request, 'users/profile.html', context)


from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from .models import CustomUser

class SignUp(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('store:home')
    template_name = 'users/signup.html'

    def form_valid(self, form):
        user = form.save(commit=False)  # Не сохраняем сразу, чтобы можно было изменить данные
        phone_number = form.cleaned_data.get("phone_number")

        user.save()  # Теперь сохраняем
        login(self.request, user)  # Авторизуем пользователя после регистрации
        
        return super().form_valid(form)


def feedback_processing(request):
    """
    Представление приема и обработки для обратной связи.
    """
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = Feedback(
                feedback_name=form.cleaned_data['feedback_name'],
                feedback_email=form.cleaned_data['feedback_email'],
                feedback_message=form.cleaned_data['feedback_message'],
            )
            feedback.save()

            # Отпрака сообщения

            return render(request, 'users/feedback_success.html')
    return render(request, 'users/feedback_failed.html')


from django.contrib.auth.decorators import login_required, user_passes_test
from store.models import Item
from django.shortcuts import get_object_or_404


def is_admin(user):
    return user.is_superuser  # ✅ Проверка на администратора

@login_required
@user_passes_test(is_admin)
def moderate_items(request):
    items = Item.objects.filter(is_approved=False)
    return render(request, "store/moderate_items.html", {"items": items})

@login_required
@user_passes_test(is_admin)
def approve_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    item.is_approved = True
    item.save()
    return redirect("users:moderate_items")

@login_required
@user_passes_test(is_admin)
def reject_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    item.delete()
    return redirect("users:moderate_items")
