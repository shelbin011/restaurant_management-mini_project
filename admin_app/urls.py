from django.urls import path
from admin_app import views

app_name = 'admin_app'

urlpatterns = [
path('', views.admin_root, name='admin_root'),
path("admin_login_page/",views.admin_login_page,name='admin_login_page'),
path("admin_login/",views.admin_login,name='admin_login'),
path('register/', views.register, name='register'),
path("delete_logout/",views.delete_logout,name='delete_logout'),
    path('index/',views.index,name='index'),
path("add_category/",views.add_category,name='add_category'),
path('view_category/', views.view_category, name='view_category'),
path('save_category/', views.save_category, name='save_category'),
path('edit_category/<int:id>/', views.edit_category, name='edit_category'),
path('update_category/<int:id>/', views.update_category, name='update_category'),
path('delete_category/<int:category_id>/', views.delete_category, name='delete_category'),
path('add_food/', views.add_food, name='add_food'),
    path('save_food/', views.save_food, name='save_food'),
    path('view_food/', views.view_food, name='view_food'),
path('toggle_availability/<int:item_id>/', views.toggle_availability, name='toggle_availability'),
path('delete_food/<int:item_id>/', views.delete_food, name='delete_food'),
path('edit_food/<int:food_id>/', views.edit_food, name='edit_food'),

    path('view_customers/', views.view_customers, name='view_customers'),
    path('view_orders/', views.view_orders, name='view_orders'),
    path('update_order_status/<str:order_id>/', views.update_order_status, name='update_order_status'),
    
    path('view_waiters/', views.view_waiters, name='view_waiters'),
    path('add_waiter/', views.add_waiter, name='add_waiter'),
    path('delete_waiter/<int:waiter_id>/', views.delete_waiter, name='delete_waiter'),




]