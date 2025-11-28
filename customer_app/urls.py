from django.urls import path
from customer_app import views

app_name = 'customer_app'

urlpatterns = [
# customer_app/urls.py
path('', views.cust_home, name='cust_home_root'),  # default landing page
path('cust_home/', views.cust_home, name='cust_home'),


path("register/", views.user_reg, name="user_reg"),
    path("user_log/", views.user_log, name="user_log"),
    path("save_reg/", views.save_reg, name="save_reg"),

    path("user_login/", views.user_login, name="user_login"),
    path("delete_user/", views.delete_user, name="delete_user"),
path('menu/', views.view_menu, name='view_menu'),
path('favorite/toggle/<int:item_id>/', views.toggle_favorite, name='toggle_favorite'),

# Cart routes
path('cart/', views.view_cart, name='view_cart'),
path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),

# Order and payment routes
path('checkout/', views.checkout, name='checkout'),
path('payment/<str:order_id>/', views.payment, name='payment'),
path('orders/', views.view_orders, name='view_orders')


]