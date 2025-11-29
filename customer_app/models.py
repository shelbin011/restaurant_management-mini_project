from django.db import models
from django.utils import timezone

# Create your models here.
class regdb(models.Model):
    Username = models.CharField(max_length=100, null=True, blank=True)
    Email = models.EmailField(max_length=100, null=True, blank=True)
    Mobile = models.IntegerField(null=True, blank=True)
    Password = models.CharField(max_length=100, null=True, blank=True)
    Confirm_password = models.CharField(max_length=100, null=True, blank=True)

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(regdb, on_delete=models.CASCADE, related_name='orders')
    order_id = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    delivery_address = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    special_instructions = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.customer.Username}"
    
    class Meta:
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey('admin_app.fooditems', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    
    def line_total(self):
        return self.price * self.quantity
    
    def __str__(self):
        return f"{self.food_item.name} x{self.quantity} - {self.order.order_id}"

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash on Delivery'),
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment for Order {self.order.order_id} - {self.status}"


class Review(models.Model):
    """Customer reviews for orders and food items"""
    RATING_CHOICES = [(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)]
    
    customer = models.ForeignKey(regdb, on_delete=models.CASCADE, related_name='reviews')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    food_item = models.ForeignKey('admin_app.fooditems', on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Review by {self.customer.Username} - {self.rating} stars"
    
    class Meta:
        ordering = ['-created_at']


class PromoCode(models.Model):
    """Discount promo codes"""
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.IntegerField(help_text="Discount percentage (0-100)")
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    usage_limit = models.IntegerField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    
    def is_valid_now(self):
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until
    
    def calculate_discount(self, order_amount):
        if not self.is_valid_now():
            return 0
        discount = (order_amount * self.discount_percent) / 100
        if self.max_discount_amount:
            discount = min(discount, float(self.max_discount_amount))
        return discount
    
    def __str__(self):
        return f"{self.code} - {self.discount_percent}% off"


class OrderStatusHistory(models.Model):
    """Track order status changes"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.ORDER_STATUS_CHOICES)
    changed_at = models.DateTimeField(default=timezone.now)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.order.order_id} - {self.status} at {self.changed_at}"
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = "Order Status Histories"