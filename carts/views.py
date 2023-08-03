from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from store.models import Product, Variation
from carts.models import Cart, CartItem

# Create your views here.


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()

    return cart


def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variations = []

    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                product_variation = Variation.objects.get(
                    product=product, 
                    variation_category__iexact=key, 
                    variation_value__iexact=value
                )
                product_variations.append(product_variation)
            except:
                pass

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
    cart.save()

    cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()

    if cart_item_exists:
        cart_item = CartItem.objects.filter(product=product, cart=cart)
        # List of product variations of items currently in cart
        product_variations_in_cart = []
        # List of ID of items currently in cart
        id_of_products_in_cart = []
        for item in cart_item:
            product_variation = item.variations.all()
            product_variations_in_cart.append(list(product_variation))
            id_of_products_in_cart.append(item.id)
        
        if product_variations in product_variations_in_cart:
            index = product_variations_in_cart.index(product_variations)
            item_id = id_of_products_in_cart[index]
            item = CartItem.objects.get(product=product, id=item_id)
            item.quantity += 1
            item.save()
        else:
            item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if len(product_variations) > 0:
                item.variations.clear()
                item.variations.add(*product_variations)
            item.save()
    else:
        cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,
            cart = cart
        )

        if len(product_variations) > 0:
            cart_item.variations.clear()
            cart_item.variations.add(*product_variations)
        cart_item.save()

    return redirect('cart') 


def remove_cart(request, product_id, cart_item_id):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        pass

    product = get_object_or_404(Product, id=product_id)

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass

    return redirect('cart')


def remove_cart_item(request, product_id, cart_item_id):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        pass

    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()

    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        cart_tax = (2 * total)/100
        grand_total = total + cart_tax
    except Cart.DoesNotExist:
        pass
    
    context = {
        'total': total,
        'quantity': quantity,
        'cart_tax': cart_tax,
        'grand_total': grand_total,
        'cart_items': cart_items
    }

    return render(request, 'store/cart.html', context)