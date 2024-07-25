import datetime
import json

from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string

from carts.models import CartItem
from store.models import Product
from .forms import OrderForm
from .models import Order, Payment, OrderProduct


def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (3 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Extract form data
            form_data = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'phone': form.cleaned_data['phone'],
                'email': form.cleaned_data['email'],
                'address_line_1': form.cleaned_data['address_line_1'],
                'address_line_2': form.cleaned_data['address_line_2'],
                'country': form.cleaned_data['country'],
                'city': form.cleaned_data['city'],
                'order_note': form.cleaned_data['order_note'],
                'order_total': grand_total,
                'tax': tax,
                'ip': request.META.get('REMOTE_ADDR'),
            }

            # Check for existing order
            existing_order = Order.objects.filter(user=current_user, is_ordered=False).first()
            if existing_order:
                # Check if details are different
                details_different = (
                        existing_order.first_name != form_data['first_name'] or
                        existing_order.last_name != form_data['last_name'] or
                        existing_order.phone != form_data['phone'] or
                        existing_order.email != form_data['email'] or
                        existing_order.address_line_1 != form_data['address_line_1'] or
                        existing_order.address_line_2 != form_data['address_line_2'] or
                        existing_order.country != form_data['country'] or
                        existing_order.city != form_data['city'] or
                        existing_order.order_note != form_data['order_note']
                )
                if details_different:
                    existing_order.delete()
                    existing_order = None

            if not existing_order:
                # Create new order
                data = Order()
                data.user = current_user
                data.first_name = form_data['first_name']
                data.last_name = form_data['last_name']
                data.phone = form_data['phone']
                data.email = form_data['email']
                data.address_line_1 = form_data['address_line_1']
                data.address_line_2 = form_data['address_line_2']
                data.country = form_data['country']
                data.city = form_data['city']
                data.order_note = form_data['order_note']
                data.order_total = form_data['order_total']
                data.tax = form_data['tax']
                data.ip = form_data['ip']
                data.save()
                order = data  # Assigning the newly created order to the order variable

                # Generate order number
                yr = int(datetime.date.today().strftime('%Y'))
                dt = int(datetime.date.today().strftime('%d'))
                mt = int(datetime.date.today().strftime('%m'))
                d = datetime.date(yr, mt, dt)
                current_date = d.strftime("%Y%m%d")
                data.order_number = current_date + str(data.id)
                data.save()
            else:
                order = existing_order

            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payment.html', context)
        else:
            return redirect('store')


def payments(request):
    body = json.loads(request.body)
    current_user = request.user
    order = Order.objects.get(user=current_user, is_ordered=False, order_number=body['orderID'])
    payment = Payment(
        user=current_user,
        payment_id=body['transactionID'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status']
    )
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart items to Order Product Table
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        order_product = OrderProduct()
        order_product.order_id = order.id
        order_product.payment = payment
        order_product.user_id = request.user.id
        order_product.product_id = item.product_id
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.ordered = True
        order_product.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        order_product = OrderProduct.objects.get(id=order_product.id)
        order_product.variations.set(product_variation)

        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product.id)
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order recieved email to customer
    mail_subject = 'Thank You For Your Order !'
    message = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Send order number and transaction id buch to sendData method wia JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id
    }
    return JsonResponse(data)


    return render(request, 'orders/payment.html')


def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        payment = Payment.objects.get(payment_id=transID)
        subtotal = 0
        for i in ordered_products:
            subtotal += i.product.price * i.quantity

        context = {
            'order': order,
            'order_number': order_number,
            'ordered_products': ordered_products,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')

