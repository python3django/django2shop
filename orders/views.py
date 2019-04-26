from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from .models import Order
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from shop.recommender import Recommender
from shop.models import Product


def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.discount
            if request.user.is_authenticated:
                order.user = request.user
            order.save()
            products = []
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'], quantity=item['quantity'])
                # создаем список продуктов чтобы добавить их в Redis для последующей рекомендации
                products.append(Product.objects.get(translations__name=item['product']))
            # clear the cart
            cart.clear()
            # order send mail
            order_mail = Order.objects.get(id=order.id)
            subject = 'Order nr. {}'.format(order_mail.id)
            message = 'Dear {},\n\nYou have successfully placed an order. Your order id is {}.'.format(
                        order_mail.first_name, order_mail.id)
            mail_sent = send_mail(subject, message, 'django2shop2@gmail.com', [order_mail.email])
            # set the order in the session
            request.session['order_id'] = order.id
            # добавляем продукт в базу данных редис (added products in redis db)
            r = Recommender()
            r.products_bought(products)
            # redirect for payment
            return redirect(reverse('payment:process'))
    else:
        form = OrderCreateForm()
    return render(request, 'orders/order/create.html', {'cart': cart, 'form': form})


@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/orders/order/detail.html', {'order': order})


@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('orders/order/pdf.html', {'order': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="order_{}.pdf"'.format(order.id)
    weasyprint.HTML(string=html).write_pdf(response, stylesheets=[weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')])
    return response


# my view
@login_required
def user_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'user/orders/order/detail.html', {'order': order})
