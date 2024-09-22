from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from carts.models import Cart, CartItem
from store.models import Product, Variation
import geonamescache
import requests

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    if request.user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
            for key, value in request.POST.items():
                if key != 'csrfmiddlewaretoken':  # Exclude CSRF token from the POST items
                    try:
                        variation = Variation.objects.get(variation_category__iexact=key, variation_value__iexact=value)
                        product_variation.append(variation)
                    except Variation.DoesNotExist:
                        redirect('home')
                        exit()

        is_cart_item_exists = CartItem.objects.filter(user=current_user).exists()
        if is_cart_item_exists:
            # Check if the cart item with the specific product and variations already exists
            for item in CartItem.objects.filter(product=product, user=current_user):
                existing_variations = item.variations.all()
                if set(existing_variations) == set(product_variation):
                    # The cart item with the exact variations exists, update quantity
                    item.quantity += 1
                    item.save()
                    break
            else:
                # No matching cart item found, create a new one
                cart_item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                cart_item.variations.set(product_variation)  # Use set() to assign variations
                cart_item.save()
        else:
            # The cart was just created, so add a new cart item
            cart_item = CartItem.objects.create(product=product, quantity=1, user=current_user)
            cart_item.variations.set(product_variation)  # Use set() to assign variations
            cart_item.save()

        return redirect('cart')
    else:
        product_variation = []
        if request.method == 'POST':
            for key, value in request.POST.items():
                if key != 'csrfmiddlewaretoken':  # Exclude CSRF token from the POST items
                    try:
                        variation = Variation.objects.get(variation_category__iexact=key, variation_value__iexact=value)
                        product_variation.append(variation)
                    except Variation.DoesNotExist:
                        redirect('home')
                        exit()

        cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))

        if not created:
            # Check if the cart item with the specific product and variations already exists
            for item in CartItem.objects.filter(product=product, cart=cart):
                existing_variations = item.variations.all()
                if set(existing_variations) == set(product_variation):
                    # The cart item with the exact variations exists, update quantity
                    item.quantity += 1
                    item.save()
                    break
            else:
                # No matching cart item found, create a new one
                cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                cart_item.variations.set(product_variation)  # Use set() to assign variations
                cart_item.save()
        else:
            # The cart was just created, so add a new cart item
            cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            cart_item.variations.set(product_variation)  # Use set() to assign variations
            cart_item.save()

        return redirect('cart')


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product,id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product,id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')


def cart(request, total=0, quantity=0,  cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (3*total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        tax = 0
        grand_total = 0
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)

def get_cities(request, country_code):
    gc = geonamescache.GeonamesCache()
    all_cities = gc.get_cities()
    filtered_cities = {city_id: city for city_id, city in all_cities.items() if city['countrycode'] == country_code}
    city_list = [{'geonameid': city['geonameid'], 'name': city['name']} for city in filtered_cities.values()]
    city_list.sort(key=lambda city: city['name'])  # Sort by city name
    return JsonResponse(city_list, safe=False)


@login_required(login_url='login')
def checkout(request, total=0, quantity=0,  cart_items=None):
    gc = geonamescache.GeonamesCache()
    countries = gc.get_countries()
    country_list = [(country['iso'], country['name']) for country in countries.values()]
    country_list.sort(key=lambda country: country[1])  # Sort by country name
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (3*total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        tax = 0
        grand_total = 0
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'countries': country_list,
    }
    return render(request, 'store/checkout.html', context)