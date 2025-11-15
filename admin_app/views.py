from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import categorydb,fooditems
from django.contrib import messages
# Create your views here.

def admin_login_page(req):
    return render(req,'adminlogin.html')

def admin_root(request):
    if 'username' in request.session:
        return redirect('admin_app:index')
    return redirect('admin_app:admin_login_page')

def admin_login(request):
    if request.method == 'POST':
        us = request.POST.get('username')
        pa = request.POST.get('password')

        # Fixed typo: should be "username__contains" not "username_contains"
        if User.objects.filter(username__contains=us).exists():
            x = authenticate(username=us, password=pa)
            if x is not None:
                login(request, x)
                request.session['username'] = us
                request.session['password'] = pa
                # Suppress success popup to avoid delayed SweetAlert on next clicks

                # Redirect to your homepage or admin dashboard
                return redirect('admin_app:index')
            else:
                messages.warning(request, "Invalid Password")
                return redirect('admin_app:admin_login_page')
        else:
            messages.warning(request, "Invalid Username")
            return redirect('admin_app:admin_login_page')

    # ⚠ ADD THIS for GET request
    return render(request, 'adminlogin.html')
def delete_logout(request):
    if 'username' in request.session:
        del request.session['username']
    if 'password' in request.session:
        del request.session['password']
    messages.success(request, "Successfully Logged Out")
    return redirect('admin_app:admin_login_page')




def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('admin_app:register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('admin_app:register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('admin_app:register')

        # Create the user
        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Registration successful! Please log in.")
        return redirect('admin_app:admin_login')

    return render(request, 'register.html')

def index(request):
    # Require admin session to access dashboard
    if 'username' not in request.session:
        messages.warning(request, "Please log in to access the admin dashboard.")
        return redirect('admin_app:admin_login_page')
    food_count = fooditems.objects.count()
    category_count = categorydb.objects.count()
    from customer_app.models import regdb, Order
    customer_count = regdb.objects.count()
    order_count = Order.objects.count()
    pending_order_count = Order.objects.filter(status='pending').count()

    recent_foods = fooditems.objects.select_related('category').order_by('-id')[:5]
    recent_customers = regdb.objects.order_by('-id')[:5]
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:5]

    context = {
        'food_count': food_count,
        'category_count': category_count,
        'customer_count': customer_count,
        'order_count': order_count,
        'pending_order_count': pending_order_count,
        'recent_foods': recent_foods,
        'recent_customers': recent_customers,
        'recent_orders': recent_orders,
    }
    return render(request, 'index.html', context)

def add_category(req):
    return render(req,"addcategory.html")

def save_category(req):
    if req.method=='POST':
        na=req.POST.get('category')
        de=req.POST.get('description')
        im=req.FILES.get('image')
        obj=categorydb(Category_name=na,Description=de,Image=im)
        obj.save()
        messages.success(req,"Category saved successfully")
        return redirect('admin_app:add_category')

def view_category(request):
    data = categorydb.objects.all()
    return render(request, 'view_category.html', {'data': data})

from django.shortcuts import render, redirect, get_object_or_404
from .models import categorydb
from customer_app.models import regdb

def edit_category(request, id):
    data = get_object_or_404(categorydb, id=id)
    return render(request, 'edit_category.html', {'data': data})

def update_category(request, id):
    if request.method == "POST":
        cat = categorydb.objects.get(id=id)
        cat.Category_name = request.POST.get('category')
        cat.Description = request.POST.get('description')
        if 'image' in request.FILES:
            cat.Image = request.FILES['image']
        cat.save()
        return redirect('admin_app:view_category')

def delete_category(request, category_id):
    category = get_object_or_404(categorydb, id=category_id)
    category.delete()
    messages.success(request, "Category deleted successfully.")
    return redirect('admin_app:view_category')



def add_food(request):
    categories = categorydb.objects.all()  # fetch all categories
    return render(request, 'add_food.html', {'categories': categories})

def save_food(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')
        # Treat missing checkbox as available by default so new items appear in menu
        available = True if request.POST.get('availability') is None else (request.POST.get('availability') == 'on')

        category = categorydb.objects.get(id=category_id)
        obj = fooditems(
            name=name,
            description=description,
            price=price,
            category=category,
            image=image,
            availability=available
        )
        obj.save()
        messages.success(request, "✅ Food item added successfully!")
        return redirect('admin_app:add_food')

def view_food(request):
    selected_category = request.GET.get('category')
    search_query = request.GET.get('q', '')
    categories = categorydb.objects.all()  # ✅ use categorydb

    # Sorting
    sort_key = request.GET.get('sort', 'name')
    sort_dir = request.GET.get('dir', 'asc')
    allowed_sort_fields = {
        'name': 'name',
        'price': 'price',
        'status': 'availability',
        'category': 'category__Category_name',
        'created': 'id',  # fallback if needed
    }
    order_field = allowed_sort_fields.get(sort_key, 'name')
    if sort_dir == 'desc':
        order_field = '-' + order_field

    from django.db.models import Q
    qs = fooditems.objects.select_related('category')
    if selected_category:
        qs = qs.filter(category_id=selected_category)
    if search_query:
        qs = qs.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__Category_name__icontains=search_query)
        )
    data = qs.order_by(order_field)

    return render(request, 'view_food.html', {
        'data': data,
        'categories': categories,
        'selected_category': int(selected_category) if selected_category else None,
        'sort': sort_key,
        'dir': sort_dir,
        'search_query': search_query,
    })

def toggle_availability(request, item_id):
    item = get_object_or_404(fooditems, id=item_id)
    item.availability = not item.availability
    item.save()
    return redirect('admin_app:view_food')

def delete_food(request, item_id):
    item = get_object_or_404(fooditems, id=item_id)
    item.delete()
    messages.success(request, "Food item deleted successfully!")
    return redirect('admin_app:view_food')

def edit_food(request, food_id):
    food = get_object_or_404(fooditems, id=food_id)
    categories = categorydb.objects.all()

    if request.method == 'POST':
        food.name = request.POST.get('name')
        food.description = request.POST.get('description')
        food.price = request.POST.get('price')
        category_id = request.POST.get('category')
        food.category = get_object_or_404(categorydb, id=category_id)

        if 'image' in request.FILES:
            food.image = request.FILES['image']

        food.save()
        messages.success(request, "Food item updated successfully!")
        return redirect('admin_app:view_food')

    return render(request, 'edit_food.html', {'food': food, 'categories': categories})



def view_customers(request):
    customers = regdb.objects.all().order_by('Username')
    return render(request, 'view_customers.html', {'customers': customers})

def view_orders(request):
    # Require admin session to access orders
    if 'username' not in request.session:
        messages.warning(request, "Please log in to access the admin dashboard.")
        return redirect('admin_app:admin_login_page')
    
    from customer_app.models import Order, OrderItem, Payment
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    
    # Base queryset with related data
    orders = Order.objects.select_related('customer', 'payment').prefetch_related('items__food_item')
    
    # Apply filters
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search_query:
        from django.db.models import Q
        orders = orders.filter(
            Q(order_id__icontains=search_query) |
            Q(customer__Username__icontains=search_query) |
            Q(customer__Email__icontains=search_query) |
            Q(contact_number__icontains=search_query)
        )
    
    # Order by creation date (newest first)
    orders = orders.order_by('-created_at')
    
    # Get order statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='completed').count()
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'status_choices': Order.ORDER_STATUS_CHOICES,
    }
    return render(request, 'view_orders.html', context)

def update_order_status(request, order_id):
    # Require admin session
    if 'username' not in request.session:
        messages.warning(request, "Please log in to access the admin dashboard.")
        return redirect('admin_app:admin_login_page')
    
    from customer_app.models import Order
    from django.shortcuts import get_object_or_404
    
    order = get_object_or_404(Order, order_id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [choice[0] for choice in Order.ORDER_STATUS_CHOICES]:
            order.status = new_status
            order.save()
            messages.success(request, f"Order {order_id} status updated to {new_status.title()}")
        else:
            messages.error(request, "Invalid status selected")
    
    return redirect('admin_app:view_orders')

def view_waiters(request):
    # Require admin session
    if 'username' not in request.session:
        messages.warning(request, "Please log in to access the admin dashboard.")
        return redirect('admin_app:admin_login_page')
    
    from waiter_app.models import Waiter
    
    waiters = Waiter.objects.select_related('user').all().order_by('display_name')
    
    context = {
        'waiters': waiters,
    }
    return render(request, 'view_waiters.html', context)

def add_waiter(request):
    # Require admin session
    if 'username' not in request.session:
        messages.warning(request, "Please log in to access the admin dashboard.")
        return redirect('admin_app:admin_login_page')
    
    from waiter_app.models import Waiter
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        display_name = request.POST.get('display_name')
        email = request.POST.get('email', '')
        
        # Validation
        if not username or not password or not display_name:
            messages.error(request, "Username, password, and display name are required!")
            return render(request, 'add_waiter.html')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'add_waiter.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return render(request, 'add_waiter.html')
        
        if email and User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return render(request, 'add_waiter.html')
        
        # Create User account
        user = User.objects.create_user(
            username=username,
            email=email if email else f"{username}@restaurant.com",
            password=password
        )
        
        # Create Waiter profile
        waiter = Waiter.objects.create(
            user=user,
            display_name=display_name
        )
        
        messages.success(request, f"Waiter '{display_name}' created successfully!")
        return redirect('admin_app:view_waiters')
    
    return render(request, 'add_waiter.html')

def delete_waiter(request, waiter_id):
    # Require admin session
    if 'username' not in request.session:
        messages.warning(request, "Please log in to access the admin dashboard.")
        return redirect('admin_app:admin_login_page')
    
    from waiter_app.models import Waiter
    from django.shortcuts import get_object_or_404
    
    waiter = get_object_or_404(Waiter, id=waiter_id)
    display_name = waiter.display_name
    user = waiter.user
    
    # Delete waiter profile and user account
    waiter.delete()
    user.delete()
    
    messages.success(request, f"Waiter '{display_name}' deleted successfully!")
    return redirect('admin_app:view_waiters')
