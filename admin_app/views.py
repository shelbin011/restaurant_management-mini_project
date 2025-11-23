from datetime import datetime, timedelta, time
import io
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import categorydb, fooditems
from customer_app.models import Order, OrderItem, Payment, regdb
from waiter_app.models import Waiter
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


def _parse_date_param(date_str, fallback_dt, end_of_day=False):
    """
    Convert a yyyy-mm-dd string into an aware datetime. Falls back to provided datetime.
    """
    parsed_date = parse_date(date_str) if date_str else None
    if parsed_date:
        combined_time = time.max if end_of_day else time.min
        candidate = datetime.combine(parsed_date, combined_time)
        aware_candidate = timezone.make_aware(candidate)
        return aware_candidate
    return fallback_dt


def _build_order_report_data(start_param, end_param, status_param):
    now = timezone.now()
    default_start = now - timedelta(days=30)
    start_dt = _parse_date_param(start_param, default_start)
    end_dt = _parse_date_param(end_param, now, end_of_day=True)

    if start_dt > end_dt:
        start_dt, end_dt = end_dt - timedelta(days=30), end_dt

    orders_qs = Order.objects.select_related('customer', 'payment').prefetch_related('items__food_item')
    filtered_orders = orders_qs.filter(created_at__range=(start_dt, end_dt))
    if status_param:
        filtered_orders = filtered_orders.filter(status=status_param)
    filtered_orders = filtered_orders.order_by('-created_at')

    status_label_map = dict(Order.ORDER_STATUS_CHOICES)

    total_orders = filtered_orders.count()
    total_revenue = filtered_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    average_order_value = (total_revenue / total_orders) if total_orders else Decimal('0.00')
    completed_orders = filtered_orders.filter(status='completed').count()
    cancelled_orders = filtered_orders.filter(status='cancelled').count()

    status_breakdown = list(
        filtered_orders.values('status').annotate(count=Count('id')).order_by('-count')
    )
    for row in status_breakdown:
        row['label'] = status_label_map.get(row['status'], row['status'].title())

    top_customers = list(
        filtered_orders.values('customer__Username')
        .annotate(order_count=Count('id'), total_spent=Sum('total_amount'))
        .order_by('-total_spent')[:5]
    )

    order_items = OrderItem.objects.filter(order__in=filtered_orders).annotate(
        line_total=ExpressionWrapper(
            F('quantity') * F('price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )

    top_items = list(
        order_items.values('food_item__name')
        .annotate(quantity=Sum('quantity'), revenue=Sum('line_total'))
        .order_by('-quantity')[:5]
    )

    daily_summary = list(
        filtered_orders.annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(order_count=Count('id'), revenue=Sum('total_amount'))
        .order_by('day')
    )

    return {
        'orders': filtered_orders,
        'start_dt': start_dt,
        'end_dt': end_dt,
        'status_filter': status_param,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'average_order_value': average_order_value,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'status_breakdown': status_breakdown,
        'top_customers': top_customers,
        'top_items': top_items,
        'daily_summary': daily_summary,
        'status_label_map': status_label_map,
        'report_generated_at': now,
    }


def order_reports(request):
    if 'username' not in request.session:
        messages.warning(request, "Please log in to access the admin dashboard.")
        return redirect('admin_app:admin_login_page')

    start_param = request.GET.get('start_date')
    end_param = request.GET.get('end_date')
    status_param = request.GET.get('status', '')

    report_data = _build_order_report_data(start_param, end_param, status_param)

    context = {
        **report_data,
        'start_date_value': report_data['start_dt'].date().isoformat(),
        'end_date_value': report_data['end_dt'].date().isoformat(),
        'status_choices': Order.ORDER_STATUS_CHOICES,
        'active_page': 'reports',
        'status_filter_label': report_data['status_label_map'].get(status_param, 'All Orders') if status_param else 'All Orders',
    }
    return render(request, 'order_reports.html', context)


def download_order_report_pdf(request):
    if 'username' not in request.session:
        messages.warning(request, "Please log in to access the admin dashboard.")
        return redirect('admin_app:admin_login_page')

    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
    except ImportError:
        messages.error(
            request,
            "PDF generation requires the ReportLab package. Please install it with 'pip install reportlab'."
        )
        return redirect('admin_app:order_reports')

    start_param = request.GET.get('start_date')
    end_param = request.GET.get('end_date')
    status_param = request.GET.get('status', '')
    report_data = _build_order_report_data(start_param, end_param, status_param)
    orders = list(report_data['orders'])

    buffer = io.BytesIO()
    page_size = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size

    def new_page():
        pdf.showPage()
        pdf.setFont("Helvetica", 10)
        return height - 50

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, height - 40, "Order Performance Report")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, height - 60, f"Date Range: {report_data['start_dt'].date()} to {report_data['end_dt'].date()}")
    pdf.drawString(40, height - 75, f"Status Filter: {report_data['status_label_map'].get(status_param, 'All') if status_param else 'All'}")
    pdf.drawString(40, height - 90, f"Generated: {report_data['report_generated_at'].strftime('%Y-%m-%d %H:%M')}")

    y = height - 120
    summary_lines = [
        f"Total Orders: {report_data['total_orders']}",
        f"Total Revenue: ₹{report_data['total_revenue']}",
        f"Average Order Value: ₹{report_data['average_order_value']}",
        f"Completed Orders: {report_data['completed_orders']}",
        f"Cancelled Orders: {report_data['cancelled_orders']}",
    ]
    for line in summary_lines:
        pdf.drawString(40, y, line)
        y -= 15

    y -= 10
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, "Orders")
    pdf.setFont("Helvetica-Bold", 10)
    y -= 20
    headers = ["ID", "Customer", "Status", "Amount", "Created"]
    col_positions = [40, 150, 320, 420, 500]
    for idx, header in enumerate(headers):
        pdf.drawString(col_positions[idx], y, header)
    y -= 15
    pdf.setFont("Helvetica", 10)

    for order in orders:
        if y < 60:
            y = new_page()
        customer_name = order.customer.Username if order.customer else "Guest"
        status_label = report_data['status_label_map'].get(order.status, order.status.title())
        pdf.drawString(col_positions[0], y, order.order_id)
        pdf.drawString(col_positions[1], y, customer_name[:25])
        pdf.drawString(col_positions[2], y, status_label)
        pdf.drawString(col_positions[3], y, f"₹{order.total_amount}")
        pdf.drawString(col_positions[4], y, order.created_at.strftime('%Y-%m-%d %H:%M'))
        y -= 15

    pdf.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="orders_report.pdf"'
    return response

def update_order_status(request, order_id):
    # Require admin session
    if 'username' not in request.session:
        messages.warning(request, "Please log in to access the admin dashboard.")
        return redirect('admin_app:admin_login_page')
    
    from customer_app.models import Order
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
    waiter = get_object_or_404(Waiter, id=waiter_id)
    display_name = waiter.display_name
    user = waiter.user
    
    # Delete waiter profile and user account
    waiter.delete()
    user.delete()
    
    messages.success(request, f"Waiter '{display_name}' deleted successfully!")
    return redirect('admin_app:view_waiters')
