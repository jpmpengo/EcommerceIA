from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product

from .cart import Cart


def cart_add(request, product_id):
    cart = Cart(request)

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True,
    )

    if product.stock <= 0:
        messages.error(
            request,
            "Ce produit est en rupture de stock.",
        )
        return redirect("products:product_detail", product.id)

    cart.add(product=product)

    messages.success(
        request,
        "Le produit a été ajouté au panier.",
    )

    return redirect("cart:cart_detail")

def cart_detail(request):
    cart = Cart(request)

    return render(
        request,
        "cart/cart_detail.html",
        {"cart": cart},
    )

def cart_increase(request, product_id):
    cart = Cart(request)

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True,
    )

    product_id_string = str(product.id)
    current_quantity = 0

    if product_id_string in cart.cart:
        current_quantity = cart.cart[product_id_string]["quantity"]

    if current_quantity >= product.stock:
        messages.warning(
            request,
            "Vous avez atteint le stock maximum disponible.",
        )
    else:
        cart.add(product=product)

    return redirect("cart:cart_detail")    



def cart_decrease(request, product_id):
    cart = Cart(request)

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    product_id_string = str(product.id)

    if product_id_string in cart.cart:
        current_quantity = cart.cart[product_id_string]["quantity"]
        cart.update_quantity(
            product=product,
            quantity=current_quantity - 1,
        )

    return redirect("cart:cart_detail")


def cart_remove(request, product_id):
    cart = Cart(request)

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    cart.remove(product)

    return redirect("cart:cart_detail")