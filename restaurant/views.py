from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from customer_app.models import regdb
from waiter_app.models import Waiter


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
