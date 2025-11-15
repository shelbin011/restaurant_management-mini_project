from django.urls import path
from waiter_app import views

app_name = 'waiter_app'

urlpatterns = [
    path('login/', views.waiter_login, name='waiter_login'),
    path('logout/', views.waiter_logout, name='waiter_logout'),
    path('', views.waiter_home, name='waiter_home'),      # /waiter_app/   → redirects to login or dashboard
    path('dashboard/', views.waiter_dashboard, name='waiter_dashboard'),
    path('orders/', views.waiter_orders, name='waiter_orders'),
    path('menu/', views.waiter_menu, name='waiter_menu'),
    path('menu/add_to_cart/<int:item_id>/', views.new_order, name='add_to_cart'),
    path('checkout/', views.waiter_checkout, name='waiter_checkout'),
    path('new_order/', views.new_order, name='new_order'),
]