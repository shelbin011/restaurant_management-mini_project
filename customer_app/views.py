from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from admin_app.models import categorydb, fooditems
from customer_app.models import regdb, Order, OrderItem, Payment
from django.http import JsonResponse
import uuid
from django.utils import timezone
from decimal import Decimal

# Create your views here.
def cust_home(request):
    cart_count = sum(request.session.get('cart', {}).values()) if 'cart' in request.session else 0
    return render(request, 'customer_home.html', { 'cart_count': cart_count })


def user_reg(request):
    return render(request,'customer_register.html')

def user_log(request):
    return render(request,'login.html')

def save_reg(req):
    if req.method=='POST':
        us=req.POST.get('username')
        em=req.POST.get('email')
        mb=req.POST.get('mobile')
        pa=req.POST.get('password')
        co=req.POST.get('confirm')
        obj=regdb(Username=us,Email=em,Mobile=mb,Password=pa,Confirm_password=co)
        if regdb.objects.filter(Username=us).exists():
            messages.warning(req,"User already exists......!")
            return redirect('customer_app:user_reg')
        elif regdb.objects.filter(Email=em).exists():
            messages.warning(req,"Email address already exists....!!")
            return redirect('customer_app:user_reg')
        obj.save()
        messages.success(req,"Registered Successfully...!!")
        return redirect('customer_app:user_log')

def user_login(request):
    if request.method == 'POST':
        us = request.POST.get('username')
        pa = request.POST.get('password')

        if not regdb.objects.filter(Username=us).exists():
            messages.warning(request, "Invalid Username or Password")
            return redirect('customer_app:user_log')

        if regdb.objects.filter(Username=us, Password=pa).exists():
            request.session['Username'] = us
            request.session['Password'] = pa
            messages.success(request, "Welcome to dine")
            return redirect('customer_app:cust_home')

        messages.warning(request, "Invalid User or Password")
        return redirect('customer_app:user_log')

    # GET or other methods -> show login page
    return redirect('customer_app:user_log')



def delete_user(request):
    # Safely remove customer session keys (avoid KeyError causing 500)
    request.session.pop('Username', None)
    request.session.pop('Password', None)
    # Also clear cart if present
    request.session.pop('cart', None)
    messages.success(request, "Logout Successfully")
    return redirect('customer_app:cust_home')



def view_menu(request):
    categories = categorydb.objects.all()
    selected_category = request.GET.get('category')
    search_query = request.GET.get('q', '')

    from django.db.models import Q
    foods_qs = fooditems.objects.select_related('category').filter(availability=True).order_by('name')

    if selected_category:
        foods_qs = foods_qs.filter(category_id=selected_category)
    if search_query:
        foods_qs = foods_qs.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__Category_name__icontains=search_query)
        )

    print("Selected category:", selected_category)
    print("Foods queryset:", list(foods_qs))

    context = {
        'categories': categories,
        'foods': foods_qs,
        'selected_category': int(selected_category) if selected_category else None,
        'search_query': search_query,
        'cart_count': sum(_get_cart(request.session).values()) if 'cart' in request.session else 0,
    }
    return render(request, 'menu.html', context)


# --- Cart Utilities ---
def _get_cart(session):
    cart = session.get('cart', {})
    return cart

def _save_cart(session, cart):
    session['cart'] = cart
    session.modified = True


def add_to_cart(request, item_id):
    if request.method != 'POST':
        return redirect('customer_app:view_menu')
    # Require login to add to cart
    if 'Username' not in request.session:
        messages.warning(request, 'You must login to order.')
        return redirect('customer_app:user_log')
    item = fooditems.objects.filter(id=item_id, availability=True).first()
    if not item:
        messages.error(request, 'Item not available')
        return redirect('customer_app:view_menu')
    cart = _get_cart(request.session)
    key = str(item_id)
    cart[key] = cart.get(key, 0) + 1
    _save_cart(request.session, cart)
    messages.success(request, f'Added {item.name} to cart')
    return redirect('customer_app:view_menu')


def remove_from_cart(request, item_id):
    if 'Username' not in request.session:
        messages.warning(request, 'You must login to modify cart.')
        return redirect('customer_app:user_log')
    cart = _get_cart(request.session)
    key = str(item_id)
    if key in cart:
        del cart[key]
        _save_cart(request.session, cart)
        messages.success(request, 'Item removed from cart')
    return redirect('customer_app:view_cart')


def update_cart_quantity(request, item_id):
    if request.method != 'POST':
        return redirect('customer_app:view_cart')
    if 'Username' not in request.session:
        messages.warning(request, 'You must login to modify cart.')
        return redirect('customer_app:user_log')
    qty = int(request.POST.get('qty', '1'))
    cart = _get_cart(request.session)
    key = str(item_id)
    if qty <= 0:
        cart.pop(key, None)
    else:
        cart[key] = qty
    _save_cart(request.session, cart)
    messages.success(request, 'Cart updated')
    return redirect('customer_app:view_cart')


def view_cart(request):
    cart = _get_cart(request.session)
    item_ids = [int(k) for k in cart.keys()]
    items = fooditems.objects.filter(id__in=item_ids)
    id_to_item = {i.id: i for i in items}
    lines = []
    total = 0
    for sid, qty in cart.items():
        iid = int(sid)
        item = id_to_item.get(iid)
        if not item:
            continue
        line_total = float(item.price) * qty
        total += line_total
        lines.append({
            'item': item,
            'qty': qty,
            'line_total': line_total,
        })
    context = {'lines': lines, 'total': total}
    return render(request, 'cart.html', context)


def checkout(request):
    if 'Username' not in request.session:
        messages.warning(request, 'You must login to proceed with checkout.')
        return redirect('customer_app:user_log')
    
    cart = _get_cart(request.session)
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('customer_app:view_cart')
    
    item_ids = [int(k) for k in cart.keys()]
    items = fooditems.objects.filter(id__in=item_ids)
    id_to_item = {i.id: i for i in items}
    lines = []
    total = 0
    
    for sid, qty in cart.items():
        iid = int(sid)
        item = id_to_item.get(iid)
        if not item:
            continue
        line_total = float(item.price) * qty
        total += line_total
        lines.append({
            'item': item,
            'qty': qty,
            'line_total': line_total,
        })
    
    customer = regdb.objects.get(Username=request.session['Username'])
    
    if request.method == 'POST':
        delivery_address = request.POST.get('delivery_address')
        contact_number = request.POST.get('contact_number')
        special_instructions = request.POST.get('special_instructions', '')
        
        if not delivery_address or not contact_number:
            messages.error(request, 'Please provide delivery address and contact number.')
            return render(request, 'checkout.html', {
                'lines': lines, 
                'total': total, 
                'customer': customer
            })
        
        # Create order
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        order = Order.objects.create(
            customer=customer,
            order_id=order_id,
            total_amount=Decimal(str(total)),
            delivery_address=delivery_address,
            contact_number=contact_number,
            special_instructions=special_instructions
        )
        
        # Create order items
        for line in lines:
            OrderItem.objects.create(
                order=order,
                food_item=line['item'],
                quantity=line['qty'],
                price=line['item'].price
            )
        
        # Clear cart
        request.session['cart'] = {}
        request.session.modified = True
        
        # Redirect to payment
        return redirect('customer_app:payment', order_id=order.order_id)
    
    context = {
        'lines': lines, 
        'total': total, 
        'customer': customer
    }
    return render(request, 'checkout.html', context)


def payment(request, order_id):
    if 'Username' not in request.session:
        messages.warning(request, 'Please login to access payment.')
        return redirect('customer_app:user_log')
    
    order = get_object_or_404(Order, order_id=order_id, customer__Username=request.session['Username'])
    
    try:
        existing_payment = order.payment
        if existing_payment.status in ['completed', 'pending']:
            messages.info(request, 'Payment already processed for this order.')
            return redirect('customer_app:view_orders')
    except Payment.DoesNotExist:
        pass  # No payment exists yet, continue
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        if not payment_method:
            messages.error(request, 'Please select a payment method.')
            return render(request, 'payment.html', {'order': order})
        
        # Create or update payment
        payment_obj, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                'amount': order.total_amount,
                'payment_method': payment_method,
                'transaction_id': f"TXN-{uuid.uuid4().hex[:12].upper()}",
                'status': 'completed' if payment_method == 'cash' else 'pending'
            }
        )
        
        if payment_method != 'cash':
            # Simulate payment processing
            payment_obj.status = 'completed'
            payment_obj.payment_date = timezone.now()
            payment_obj.save()
        
        order.status = 'confirmed'
        order.save()
        
        messages.success(request, f'Payment successful! Order {order.order_id} is confirmed.')
        return redirect('customer_app:view_orders')
    
    return render(request, 'payment.html', {'order': order})


def view_orders(request):
    if 'Username' not in request.session:
        messages.warning(request, 'Please login to view your orders.')
        return redirect('customer_app:user_log')
    
    customer = get_object_or_404(regdb, Username=request.session['Username'])
    orders = Order.objects.filter(customer=customer).prefetch_related('items__food_item', 'payment')
    
    context = {
        'orders': orders,
        'cart_count': sum(_get_cart(request.session).values()) if 'cart' in request.session else 0,
    }
    return render(request, 'orders.html', context)

