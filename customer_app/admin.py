from django.contrib import admin
from customer_app.models import Review, PromoCode, OrderStatusHistory, Order, OrderItem, Payment

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'order', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('customer__Username', 'comment')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Order Info', {'fields': ('customer', 'order', 'food_item')}),
        ('Review', {'fields': ('rating', 'comment')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

@admin.register(PromoCode)
class PromocodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'is_active', 'valid_from', 'valid_until', 'usage_count')
    list_filter = ('is_active', 'valid_from', 'valid_until')
    search_fields = ('code',)
    readonly_fields = ('created_at', 'usage_count')
    
    fieldsets = (
        ('Promo Details', {'fields': ('code', 'discount_percent', 'max_discount_amount')}),
        ('Validity', {'fields': ('valid_from', 'valid_until', 'is_active')}),
        ('Limits', {'fields': ('min_order_amount', 'usage_limit', 'usage_count')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'status', 'changed_at', 'updated_by')
    list_filter = ('status', 'changed_at')
    search_fields = ('order__order_id',)
    readonly_fields = ('changed_at',)
    
    fieldsets = (
        ('Order Info', {'fields': ('order', 'status')}),
        ('Change Details', {'fields': ('updated_by', 'note', 'changed_at')}),
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_id', 'customer__Username')
    readonly_fields = ('order_id', 'created_at')
    
    fieldsets = (
        ('Order Info', {'fields': ('order_id', 'customer', 'status')}),
        ('Delivery', {'fields': ('delivery_address', 'contact_number', 'special_instructions')}),
        ('Amount', {'fields': ('total_amount',)}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'food_item', 'quantity', 'price')
    list_filter = ('order__created_at',)
    search_fields = ('order__order_id', 'food_item__name')
    
    fieldsets = (
        ('Order Item', {'fields': ('order', 'food_item')}),
        ('Details', {'fields': ('quantity', 'price')}),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'payment_method', 'status', 'amount', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('order__order_id',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Order Info', {'fields': ('order',)}),
        ('Payment Details', {'fields': ('payment_method', 'status', 'amount')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

