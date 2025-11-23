from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from admin_app.models import categorydb, fooditems
from customer_app.models import regdb, Order, OrderItem, Payment
from waiter_app.models import Waiter
from decimal import Decimal
import uuid
from django.utils import timezone

def waiter_home(request):
    # Redirect to login if not authenticated, otherwise redirect to dashboard
    if 'waiter_id' not in request.session:
        return redirect('waiter_app:waiter_login')
    return redirect('waiter_app:waiter_dashboard')

def waiter_login(request):
    # All GET requests should go to the unified login page
    if request.method == 'GET':
        return redirect('login')

    # Keep POST handling for compatibility if something posts directly to this view
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        try:
            waiter = Waiter.objects.get(user=user)
            auth_login(request, user)
            request.session['waiter_id'] = waiter.id
            request.session['waiter_name'] = waiter.display_name
            messages.success(request, f'Welcome, {waiter.display_name}!')
            return redirect('waiter_app:waiter_dashboard')
        except Waiter.DoesNotExist:
            messages.error(request, 'This user is not registered as a waiter.')
    else:
        messages.error(request, 'Invalid username or password.')
    return redirect('login')

def waiter_logout(request):
    if 'waiter_id' in request.session:
        del request.session['waiter_id']
    if 'waiter_name' in request.session:
        del request.session['waiter_name']
    # Clear waiter cart if exists
    if 'waiter_cart' in request.session:
        del request.session['waiter_cart']
    messages.success(request, 'Logged out successfully.')
    return redirect('waiter_app:waiter_login')

def waiter_dashboard(request):
    if 'waiter_id' not in request.session:
        messages.warning(request, 'Please login first.')
        return redirect('waiter_app:waiter_login')
    
    waiter_id = request.session['waiter_id']
    waiter = get_object_or_404(Waiter, id=waiter_id)
    
    # Get recent orders assigned to this waiter
    recent_orders = Order.objects.filter(waiter=waiter).order_by('-created_at')[:5]
    
    # Get orders statistics
    total_orders = Order.objects.filter(waiter=waiter).count()
    pending_orders = Order.objects.filter(waiter=waiter, status='pending').count()
    active_orders = Order.objects.filter(waiter=waiter, status__in=['pending', 'confirmed', 'preparing']).count()
    
    context = {
        'waiter': waiter,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'active_orders': active_orders,
    }
    return render(request, 'waiter_dashboard.html', context)

def waiter_orders(request):
    if 'waiter_id' not in request.session:
        messages.warning(request, 'Please login first.')
        return redirect('waiter_app:waiter_login')
    
    waiter_id = request.session['waiter_id']
    waiter = get_object_or_404(Waiter, id=waiter_id)
    
    # Get status filter
    status_filter = request.GET.get('status', '')
    
    # Base queryset - orders assigned to this waiter
    orders = Order.objects.filter(waiter=waiter).prefetch_related('items__food_item', 'payment', 'customer').order_by('-created_at')
    
    # Apply status filter if provided
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Handle status update
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        
        try:
            order = Order.objects.get(id=order_id, waiter=waiter)
            order.status = new_status
            order.save()
            messages.success(request, f'Order {order.order_id} status updated to {new_status}.')
            return redirect('waiter_app:waiter_orders')
        except Order.DoesNotExist:
            messages.error(request, 'Order not found.')
    
    context = {
        'orders': orders,
        'waiter': waiter,
        'status_filter': status_filter,
        'status_choices': Order.ORDER_STATUS_CHOICES,
    }
    return render(request, 'waiter_orders.html', context)

def waiter_menu(request):
    if 'waiter_id' not in request.session:
        messages.warning(request, 'Please login first.')
        return redirect('waiter_app:waiter_login')
    
    # Initialize waiter cart if not exists
    if 'waiter_cart' not in request.session:
        request.session['waiter_cart'] = {}
        request.session.modified = True
    
    # Handle add to cart from menu page
    if request.method == 'POST' and request.POST.get('action') == 'add_to_cart':
        item_id = request.POST.get('item_id')
        item = get_object_or_404(fooditems, id=item_id, availability=True)
        cart = _get_waiter_cart(request.session)
        key = str(item_id)
        cart[key] = cart.get(key, 0) + 1
        _save_waiter_cart(request.session, cart)
        messages.success(request, f'Added {item.name} to cart.')
        return redirect('waiter_app:waiter_menu')
    
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
    
    # Get cart count for waiter
    cart_count = sum(_get_waiter_cart(request.session).values()) if 'waiter_cart' in request.session else 0
    
    context = {
        'categories': categories,
        'foods': foods_qs,
        'selected_category': int(selected_category) if selected_category else None,
        'search_query': search_query,
        'cart_count': cart_count,
    }
    return render(request, 'waiter_menu.html', context)

def new_order(request):
    if 'waiter_id' not in request.session:
        messages.warning(request, 'Please login first.')
        return redirect('waiter_app:waiter_login')
    
    waiter_id = request.session['waiter_id']
    waiter = get_object_or_404(Waiter, id=waiter_id)
    
    # Initialize waiter cart if not exists
    if 'waiter_cart' not in request.session:
        request.session['waiter_cart'] = {}
        request.session.modified = True
    
    cart = _get_waiter_cart(request.session)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_to_cart':
            item_id = request.POST.get('item_id')
            item = get_object_or_404(fooditems, id=item_id, availability=True)
            key = str(item_id)
            cart[key] = cart.get(key, 0) + 1
            _save_waiter_cart(request.session, cart)
            messages.success(request, f'Added {item.name} to cart.')
            return redirect('waiter_app:waiter_menu')
        
        elif action == 'remove_from_cart':
            item_id = request.POST.get('item_id')
            key = str(item_id)
            if key in cart:
                del cart[key]
                _save_waiter_cart(request.session, cart)
                messages.success(request, 'Item removed from cart.')
            return redirect('waiter_app:waiter_checkout')
        
        elif action == 'update_quantity':
            item_id = request.POST.get('item_id')
            qty = int(request.POST.get('qty', '1'))
            key = str(item_id)
            if qty <= 0:
                cart.pop(key, None)
            else:
                cart[key] = qty
            _save_waiter_cart(request.session, cart)
            messages.success(request, 'Cart updated.')
            return redirect('waiter_app:waiter_checkout')
        
        elif action == 'clear_cart':
            request.session['waiter_cart'] = {}
            request.session.modified = True
            messages.info(request, 'Cart cleared.')
            return redirect('waiter_app:waiter_checkout')
    
    # Redirect to menu if cart is empty
    if not cart:
        messages.info(request, 'Your cart is empty. Add items from the menu.')
        return redirect('waiter_app:waiter_menu')
    
    return redirect('waiter_app:waiter_checkout')

def waiter_checkout(request):
    if 'waiter_id' not in request.session:
        messages.warning(request, 'Please login first.')
        return redirect('waiter_app:waiter_login')
    
    waiter_id = request.session['waiter_id']
    waiter = get_object_or_404(Waiter, id=waiter_id)
    
    # Initialize waiter cart if not exists
    if 'waiter_cart' not in request.session:
        request.session['waiter_cart'] = {}
        request.session.modified = True
    
    cart = _get_waiter_cart(request.session)
    
    # Handle POST requests
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Handle cart actions first
        if action == 'remove_from_cart':
            item_id = request.POST.get('item_id')
            key = str(item_id)
            if key in cart:
                del cart[key]
                _save_waiter_cart(request.session, cart)
                messages.success(request, 'Item removed from cart.')
            return redirect('waiter_app:waiter_checkout')
        
        elif action == 'update_quantity':
            item_id = request.POST.get('item_id')
            qty = int(request.POST.get('qty', '1'))
            key = str(item_id)
            if qty <= 0:
                cart.pop(key, None)
            else:
                cart[key] = qty
            _save_waiter_cart(request.session, cart)
            messages.success(request, 'Cart updated.')
            return redirect('waiter_app:waiter_checkout')
        
        elif action == 'clear_cart':
            request.session['waiter_cart'] = {}
            request.session.modified = True
            messages.info(request, 'Cart cleared.')
            return redirect('waiter_app:waiter_checkout')
    
    # Check if cart is empty
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('waiter_app:waiter_menu')
    
    # Calculate cart totals
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
    
    # Handle place order
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'place_order':
            table_number = request.POST.get('table_number')
            special_instructions = request.POST.get('special_instructions', '').strip()
            
            # Validate required fields
            if not table_number:
                messages.error(request, 'Please provide table number.')
                return render(request, 'waiter_checkout.html', {
                    'lines': lines,
                    'total': total,
                    'waiter': waiter
                })
            
            # Create or get a generic dine-in customer for waiter orders
            customer, created = regdb.objects.get_or_create(
                Username='DINE-IN-CUSTOMER',
                defaults={
                    'Email': 'dinein@restaurant.com',
                    'Mobile': 0,
                    'Password': 'dinein',
                    'Confirm_password': 'dinein'
                }
            )
            
            # Create order
            order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
            order = Order.objects.create(
                customer=customer,
                order_id=order_id,
                total_amount=Decimal(str(total)),
                order_type='dine-in',
                table_number=int(table_number),
                waiter=waiter,
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
            
            # Create payment record (cash payment for dine-in)
            Payment.objects.create(
                order=order,
                amount=order.total_amount,
                payment_method='cash',
                status='pending',  # Will be completed when bill is paid
                transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}"
            )
            
            # Clear cart
            request.session['waiter_cart'] = {}
            request.session.modified = True
            
            messages.success(request, f'Order {order.order_id} placed successfully for Table {table_number}.')
            return redirect('waiter_app:waiter_orders')
    
    context = {
        'lines': lines,
        'total': total,
        'waiter': waiter
    }
    return render(request, 'waiter_checkout.html', context)


# --- Waiter Cart Utilities ---
def _get_waiter_cart(session):
    cart = session.get('waiter_cart', {})
    return cart

def _save_waiter_cart(session, cart):
    session['waiter_cart'] = cart
    session.modified = True





