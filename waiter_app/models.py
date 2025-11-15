from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Waiter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100)
    def __str__(self):
        return self.display_name

from customer_app.models import Order
Order.add_to_class('order_type', models.CharField(max_length=10, choices=[('dine-in', 'Dine-In'), ('takeaway', 'Takeaway')], default='dine-in'))
Order.add_to_class('table_number', models.PositiveIntegerField(null=True, blank=True))
Order.add_to_class('waiter', models.ForeignKey('waiter_app.Waiter', null=True, blank=True, on_delete=models.SET_NULL))
