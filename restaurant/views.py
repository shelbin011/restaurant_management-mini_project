from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from customer_app.models import regdb
from waiter_app.models import Waiter
from django.conf import settings
from django.http import JsonResponse
import os
from admin_app.models import fooditems


def unified_login(request):
    """Unified role-based login for Admin (Django User), Waiter (Django User + Waiter profile), and Customer (regdb).

    POST: attempt Django auth first (admin/waiter). If Django user found, redirect to waiter or admin dashboard.
    If Django auth fails, try customer regdb authentication (legacy)."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Try Django auth (admin / waiter)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if this user has a Waiter profile
            try:
                waiter = Waiter.objects.get(user=user)
                # login and set waiter session keys (match existing app behavior)
                auth_login(request, user)
                request.session['waiter_id'] = waiter.id
                request.session['waiter_name'] = waiter.display_name
                messages.success(request, f'Welcome, {waiter.display_name}!')
                return redirect('waiter_app:waiter_dashboard')
            except Waiter.DoesNotExist:
                # Treat as admin/staff user
                auth_login(request, user)
                request.session['username'] = username
                # preserve existing behavior (some views read password from session)
                request.session['password'] = password
                return redirect('admin_app:index')

        # Try legacy customer regdb authentication
        try:
            cust = regdb.objects.filter(Username=username, Password=password).first()
            if cust:
                request.session['Username'] = username
                messages.success(request, f'Welcome, {username}!')
                return redirect('customer_app:cust_home')
        except Exception:
            # in case regdb table is absent or other DB issue, fall through
            pass

        messages.error(request, 'Invalid username or password.')
        return redirect('login')

    # GET -> render a generic login template. Prefer project-level template `login.html` if present,
    # otherwise fall back to customer login template.
    try:
        return render(request, 'login.html')
    except Exception:
        return render(request, 'customer_app/login.html')


def unified_logout(request):
    # Clear all known session keys used by apps
    for key in ('waiter_id', 'waiter_name', 'Username', 'username', 'password'):
        if key in request.session:
            del request.session[key]
    try:
        auth_logout(request)
    except Exception:
        pass
    messages.success(request, 'Logged out successfully.')
    return redirect('login')


def debug_media_check(request):
    """Development helper: return a JSON list of food items with image URL and file existence.

    Only enabled when DEBUG is True or SERVE_MEDIA=1 is set to avoid exposing in production.
    """
    serve_media = settings.DEBUG or os.environ.get('SERVE_MEDIA') == '1'
    if not serve_media:
        return JsonResponse({'error': 'media check disabled'}, status=403)

    rows = []
    for it in fooditems.objects.all():
        img_field = it.image.name if it.image else ''
        # build URL and filesystem path
        url = it.image.url if it.image else ''
        fs_path = os.path.join(settings.MEDIA_ROOT, img_field) if img_field else ''
        exists = os.path.exists(fs_path) if fs_path else False
        rows.append({'id': it.id, 'name': it.name, 'image_name': img_field, 'image_url': url, 'file_exists': exists, 'fs_path': fs_path})
    return JsonResponse(rows, safe=False)
