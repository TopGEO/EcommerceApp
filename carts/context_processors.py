from .models import Cart, CartItem
from .views import _cart_id


def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart)
            for i in range(len(cart_items)):
                    cart_count += 1
        except Cart.DoesNotExist:
            cart_count = 0
    return {'cart_count': cart_count}