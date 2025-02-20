document.addEventListener("DOMContentLoaded", () => {
    const updateCartItem = async (cartItemId, newQuantity, cartId) => {
      try {
        const response = await fetch("/cart/update_cart_item/", {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
          },
          body: new URLSearchParams({
            cart_item_id: cartItemId,
            new_quantity: newQuantity,
            cart_id: cartId,
          }),
        });
  
        if (!response.ok) {
          throw new Error("Ошибка при обновлении корзины");
        }
  
        const data = await response.json();
        if (data.success) {
          // Обновляем отображение количества и цен
          const quantityInput = document.querySelector(`.quantity-input[data-cart-item-id="${data.cart_item_id}"]`);
          const itemPriceElement = document.querySelector(`.cart-item-total-price[data-cart-item-id="${data.cart_item_id}"]`);
          const cartTotalPriceElement = document.querySelector("#cart-total-price");
  
          quantityInput.value = data.cart_item_quantity;
          itemPriceElement.textContent = data.cart_item_total_price;
          cartTotalPriceElement.textContent = data.cart_total_price;  
          const itemTitle = itemPriceElement.closest('tr').querySelector('td a').textContent;
          if (newQuantity >= 10) {
            itemPriceElement.dataset.originalText = itemPriceElement.textContent;
            itemPriceElement.textContent = `${data.cart_item_total_price} (опт)`;
          } else {
            if (itemPriceElement.dataset.originalText) {
              itemPriceElement.textContent = itemPriceElement.dataset.originalText;
              delete itemPriceElement.dataset.originalText;
            }
          }
        } else {
          console.error("Ошибка при обновлении данных корзины");
        }
      } catch (error) {
        console.error("Ошибка:", error);
      }
    };
    document.querySelectorAll(".plus").forEach((button) => {
      button.addEventListener("click", () => {
        const cartItemId = button.dataset.cartItemId;
        const quantityInput = document.querySelector(`.quantity-input[data-cart-item-id="${cartItemId}"]`);
        const cartId = document.querySelector("#cart-total-price").dataset.cartId;
        // Get the maximum quantity from the data attribute on the item row
        const maxQuantity = parseInt(button.closest('tr').dataset.maxQuantity) || Infinity;
    
        let newQuantity = Math.min(parseInt(quantityInput.value) + 1, maxQuantity);
        updateCartItem(cartItemId, newQuantity, cartId, maxQuantity);
      });
    });
  
    document.querySelectorAll(".minus").forEach((button) => {
      button.addEventListener("click", () => {
        const cartItemId = button.dataset.cartItemId;
        const quantityInput = document.querySelector(`.quantity-input[data-cart-item-id="${cartItemId}"]`);
        const cartId = document.querySelector("#cart-total-price").dataset.cartId;
  
        let newQuantity = Math.max(parseInt(quantityInput.value) - 1, 1); // Минимальное значение - 1
        updateCartItem(cartItemId, newQuantity, cartId);
      });
    });
  
    document.querySelectorAll(".quantity-input").forEach((input) => {
      input.addEventListener("change", () => {
        const cartItemId = input.dataset.cartItemId;
        const cartId = document.querySelector("#cart-total-price").dataset.cartId;
        const maxQuantity = parseInt(input.closest('tr').dataset.maxQuantity) || Infinity;
        let newQuantity = Math.max(parseInt(input.value), 1); // Минимальное значение - 1
        updateCartItem(cartItemId, newQuantity, cartId);
      });
    });
  });
  