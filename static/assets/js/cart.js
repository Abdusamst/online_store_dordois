document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM полностью загружен");
  
  // Проверка, что кнопки найдены
  const plusButtons = document.querySelectorAll(".plus");
  const minusButtons = document.querySelectorAll(".minus");
  console.log("Найдено кнопок плюс:", plusButtons.length);
  console.log("Найдено кнопок минус:", minusButtons.length);

  const updateCartItem = async (cartItemId, newQuantity, cartId) => {
    console.log("Вызов updateCartItem с параметрами:", { cartItemId, newQuantity, cartId });
    try {
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
      console.log("CSRF токен:", csrfToken);
      
      const response = await fetch("/cart/update_cart_item/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrfToken,
        },
        body: new URLSearchParams({
          cart_item_id: cartItemId,
          new_quantity: newQuantity,
          cart_id: cartId,
        }),
      });

      console.log("Ответ сервера:", response.status);
      
      if (!response.ok) {
        throw new Error(`Ошибка при обновлении корзины: ${response.status}`);
      }

      const data = await response.json();
      console.log("Данные от сервера:", data);
      
      if (data.success) {
        // Обновляем отображение количества и цен
        const quantityInput = document.querySelector(`.quantity-input[data-cart-item-id="${data.cart_item_id}"]`);
        const itemPriceElement = document.querySelector(`.cart-item-total-price[data-cart-item-id="${data.cart_item_id}"]`);
        const cartTotalPriceElement = document.querySelector("#cart-total-price");

        console.log("Найдены элементы для обновления:", {
          quantityInput: !!quantityInput,
          itemPriceElement: !!itemPriceElement,
          cartTotalPriceElement: !!cartTotalPriceElement
        });

        // Обновляем количество
        quantityInput.value = data.cart_item_quantity;
        
        // Если есть оптовая цена и использовать оптовую цену
        if (data.use_wholesale && data.cart_item_wholesale_price) {
          itemPriceElement.textContent = `${data.cart_item_wholesale_price} (опт)`;
        } else {
          // Иначе используем обычную цену с учетом атрибутов
          itemPriceElement.textContent = data.cart_item_total_price;
        }
        
        // Обновляем общую сумму корзины
        cartTotalPriceElement.textContent = data.cart_total_price;
        console.log("Обновление DOM завершено");
      } else {
        console.error("Ошибка при обновлении данных корзины:", data.error);
      }
    } catch (error) {
      console.error("Ошибка:", error);
    }
  };

  document.querySelectorAll(".plus").forEach((button) => {
    console.log("Добавление обработчика для кнопки плюс:", button);
    button.addEventListener("click", (event) => {
      console.log("Клик по кнопке плюс");
      const cartItemId = button.dataset.cartItemId;
      const quantityInput = document.querySelector(`.quantity-input[data-cart-item-id="${cartItemId}"]`);
      const cartId = document.querySelector("#cart-total-price").dataset.cartId;
      const maxQuantity = parseInt(button.closest('tr').dataset.maxQuantity) || Infinity;
      
      console.log("Данные кнопки плюс:", {
        cartItemId,
        currentValue: quantityInput ? quantityInput.value : "не найдено",
        cartId,
        maxQuantity
      });
  
      if (!quantityInput) {
        console.error("Не найден элемент ввода количества");
        return;
      }
  
      let newQuantity = Math.min(parseInt(quantityInput.value) + 1, maxQuantity);
      console.log("Новое количество:", newQuantity);
      updateCartItem(cartItemId, newQuantity, cartId);
      event.preventDefault(); // Предотвратить действие по умолчанию
    });
  });

  document.querySelectorAll(".minus").forEach((button) => {
    console.log("Добавление обработчика для кнопки минус:", button);
    button.addEventListener("click", (event) => {
      console.log("Клик по кнопке минус");
      const cartItemId = button.dataset.cartItemId;
      const quantityInput = document.querySelector(`.quantity-input[data-cart-item-id="${cartItemId}"]`);
      const cartId = document.querySelector("#cart-total-price").dataset.cartId;

      console.log("Данные кнопки минус:", {
        cartItemId,
        currentValue: quantityInput ? quantityInput.value : "не найдено",
        cartId
      });

      if (!quantityInput) {
        console.error("Не найден элемент ввода количества");
        return;
      }

      let newQuantity = Math.max(parseInt(quantityInput.value) - 1, 1);
      console.log("Новое количество:", newQuantity);
      updateCartItem(cartItemId, newQuantity, cartId);
      event.preventDefault(); // Предотвратить действие по умолчанию
    });
  });

  document.querySelectorAll(".quantity-input").forEach((input) => {
    input.addEventListener("change", () => {
      console.log("Изменение ввода количества");
      const cartItemId = input.dataset.cartItemId;
      const cartId = document.querySelector("#cart-total-price").dataset.cartId;
      const maxQuantity = parseInt(input.closest('tr').dataset.maxQuantity) || Infinity;
      
      console.log("Данные ввода количества:", {
        cartItemId,
        currentValue: input.value,
        cartId,
        maxQuantity
      });
      
      let newQuantity = Math.max(parseInt(input.value), 1);
      newQuantity = Math.min(newQuantity, maxQuantity);
      console.log("Новое количество:", newQuantity);
      updateCartItem(cartItemId, newQuantity, cartId);
    });
  });
});