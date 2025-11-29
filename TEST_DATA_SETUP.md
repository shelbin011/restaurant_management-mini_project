# Test Data Setup Guide

This guide helps you quickly set up test data to verify all the new advanced features.

## Quick Setup Script

You can create test data using Django shell. Run this in your terminal:

```bash
python manage.py shell
```

Then copy and paste the following code:

```python
from django.utils import timezone
from datetime import timedelta
from customer_app.models import regdb, PromoCode
from admin_app.models import fooditems

# 1. Create a test customer (if not exists)
test_customer, created = regdb.objects.get_or_create(
    Username='testcustomer',
    defaults={
        'Email': 'testcustomer@example.com',
        'Mobile': '9876543210',
        'Password': 'test@123',
        'Confirm_password': 'test@123'
    }
)
print(f"Customer: {test_customer.Username} ({'Created' if created else 'Already exists'})")

# 2. Create test promo codes
promo_codes = [
    {
        'code': 'SAVE10',
        'discount_percent': 10,
        'max_discount_amount': 500,
        'min_order_amount': 100,
        'usage_limit': 100,
    },
    {
        'code': 'WELCOME20',
        'discount_percent': 20,
        'max_discount_amount': 1000,
        'min_order_amount': 500,
        'usage_limit': 50,
    },
    {
        'code': 'WELCOME5',
        'discount_percent': 5,
        'max_discount_amount': 200,
        'min_order_amount': 50,
        'usage_limit': None,  # Unlimited
    },
]

now = timezone.now()

for promo_data in promo_codes:
    promo, created = PromoCode.objects.get_or_create(
        code=promo_data['code'],
        defaults={
            'discount_percent': promo_data['discount_percent'],
            'max_discount_amount': promo_data['max_discount_amount'],
            'min_order_amount': promo_data['min_order_amount'],
            'usage_limit': promo_data['usage_limit'],
            'is_active': True,
            'valid_from': now - timedelta(days=1),
            'valid_until': now + timedelta(days=30),
        }
    )
    status = 'Created' if created else 'Already exists'
    print(f"PromoCode: {promo.code} ({status}) - {promo.discount_percent}% off")

print("\n✓ Test data setup complete!")
```

---

## Manual Setup via Django Admin

### 1. Login to Admin Panel
- URL: `http://localhost:8000/admin/`
- Username: your admin username
- Password: your admin password

### 2. Create PromoCode
1. Go to **PromoCode** section
2. Click "Add Promo Code"
3. Fill in details:
   - **Code**: `SAVE10`
   - **Discount Percent**: `10`
   - **Max Discount Amount**: `500` (optional)
   - **Min Order Amount**: `100`
   - **Valid From**: Today's date
   - **Valid Until**: 30 days from now
   - **Usage Limit**: `100` (optional)
4. Check **Is Active** ✓
5. Click "Save"

### 3. Repeat for other codes
- `WELCOME20`: 20% discount, min ₹500
- `WELCOME5`: 5% discount, min ₹50

---

## Testing Workflow

### Test 1: Browse Menu and Apply Promo
1. Open app in browser
2. Login as customer
3. Browse menu and add items to cart (total > ₹100)
4. Go to checkout
5. Enter promo code: `SAVE10`
6. Click "Apply"
7. ✓ Verify: Discount is calculated and displayed
8. ✓ Verify: Final total is reduced

### Test 2: Place Order with Promo
1. Continue from Test 1
2. Fill delivery details
3. Click "Proceed to Payment"
4. ✓ Verify: Order is created with discounted amount
5. Complete payment

### Test 3: View Order Details
1. Go to "My Orders"
2. Click "View Details & Track" on recent order
3. ✓ Verify: Order details are displayed
4. ✓ Verify: Status timeline is shown
5. ✓ Verify: Review form is available (if not reviewed)

### Test 4: Submit Review
1. Continue from Test 3
2. Fill review form:
   - Rating: 5 stars
   - Comment: "Great food and fast delivery!"
3. Click "Submit Review"
4. ✓ Verify: Review submitted successfully message appears
5. ✓ Verify: Review is now displayed on order detail page

### Test 5: Check Admin Panel
1. Login to admin panel (`/admin/`)
2. Go to **PromoCode** section
   - ✓ Verify: `SAVE10` has usage_count = 1
3. Go to **Review** section
   - ✓ Verify: Your review is listed with rating 5
4. Go to **Order** section
   - ✓ Verify: Order is listed with status
5. Go to **Order Status History** section
   - ✓ Verify: Status change is recorded

---

## Test Data Queries

### Check PromoCode Usage
```python
from customer_app.models import PromoCode

code = PromoCode.objects.get(code='SAVE10')
print(f"Code: {code.code}")
print(f"Total Uses: {code.usage_count}")
print(f"Usage Limit: {code.usage_limit}")
print(f"Discount: {code.discount_percent}%")
print(f"Valid: {code.is_valid_now()}")
```

### Check Reviews
```python
from customer_app.models import Review

reviews = Review.objects.all()
for review in reviews:
    print(f"Order {review.order.order_id}: {review.rating}★ - {review.comment}")
```

### Check Order Status History
```python
from customer_app.models import Order

order = Order.objects.latest('created_at')
for status in order.status_history.all():
    print(f"{status.status} at {status.changed_at} by {status.updated_by}")
```

---

## Reset Test Data

### Delete All Promo Codes
```python
from customer_app.models import PromoCode
PromoCode.objects.all().delete()
print("All promo codes deleted")
```

### Delete All Reviews
```python
from customer_app.models import Review
Review.objects.all().delete()
print("All reviews deleted")
```

### Delete All Orders
```python
from customer_app.models import Order
Order.objects.all().delete()
print("All orders deleted")
```

### Complete Database Reset (Development Only)
```bash
# Delete database
rm db.sqlite3

# Create new database
python manage.py migrate

# Create new admin user
python manage.py createsuperuser
```

---

## Test Cases & Expected Results

### Test Case 1: Valid Promo Code
**Input**: Code = "SAVE10", Order Amount = ₹500
**Expected**: Discount = ₹50 (10% of 500)
**Actual**: ___________

### Test Case 2: Minimum Order Not Met
**Input**: Code = "SAVE10", Order Amount = ₹50
**Expected**: Error - "Minimum order amount required: ₹100"
**Actual**: ___________

### Test Case 3: Promo Code Expired
**Input**: Code = expired promo, Order Amount = ₹500
**Expected**: Error - "Promo code has expired"
**Actual**: ___________

### Test Case 4: Review Submission
**Input**: Rating = 5, Comment = "Good"
**Expected**: Review saved and displayed
**Actual**: ___________

### Test Case 5: Admin Panel Access
**Input**: Navigate to /admin/review
**Expected**: All reviews listed with ratings
**Actual**: ___________

---

## Performance Testing

### Load Test Promo Codes
```python
from customer_app.models import PromoCode
from django.utils import timezone
from datetime import timedelta

# Create 100 promo codes
for i in range(100):
    PromoCode.objects.create(
        code=f'PROMO{i:03d}',
        discount_percent=i % 50 + 1,
        min_order_amount=100 * (i % 10),
        is_active=True,
        valid_from=timezone.now(),
        valid_until=timezone.now() + timedelta(days=30)
    )
print("Created 100 promo codes")
```

### Test Query Performance
```python
from django.test.utils import override_settings
from django.conf import settings

# Time a promo code lookup
import time
start = time.time()
for _ in range(1000):
    code = PromoCode.objects.get(code='SAVE10')
end = time.time()
print(f"1000 queries in {end - start:.2f}s")
```

---

## Browser Testing Checklist

- [ ] Add items to cart on mobile (test responsive grid)
- [ ] Promo code applies on both desktop and mobile
- [ ] Order detail page displays correctly on mobile
- [ ] Review form is usable on mobile
- [ ] All buttons are clickable without overlap
- [ ] Images load correctly
- [ ] Messages display properly

---

## Common Issues & Fixes

### Issue: Promo code shows "Not found"
**Fix**: 
1. Check spelling in admin panel
2. Verify "Is Active" is checked
3. Check date range (valid_from <= now <= valid_until)

### Issue: Review form not appearing
**Fix**:
1. Logout and login again
2. Check order status (must be completed to review)
3. Check browser console for JavaScript errors

### Issue: Discount not reflecting in total
**Fix**:
1. Hard refresh page (Ctrl+F5)
2. Check JavaScript console for errors
3. Verify promo code response in Network tab

### Issue: Admin panel shows "no data"
**Fix**:
1. Run migrations: `python manage.py migrate`
2. Check database: `python manage.py shell`
3. Restart Django server

---

## Automated Test Suite (Optional)

Create `test_advanced_features.py`:

```python
from django.test import TestCase
from customer_app.models import PromoCode, Review, Order
from django.utils import timezone
from datetime import timedelta

class PromoCodeTestCase(TestCase):
    def setUp(self):
        now = timezone.now()
        self.promo = PromoCode.objects.create(
            code='TEST10',
            discount_percent=10,
            min_order_amount=100,
            is_active=True,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30)
        )
    
    def test_promo_is_valid_now(self):
        self.assertTrue(self.promo.is_valid_now())
    
    def test_promo_calculate_discount(self):
        discount = self.promo.calculate_discount(1000)
        self.assertEqual(discount, 100)
```

Run with:
```bash
python manage.py test customer_app.tests
```

---

## Next Steps

After testing, consider:
1. [ ] Deploy to Render
2. [ ] Monitor promo code usage
3. [ ] Collect customer feedback from reviews
4. [ ] Create new marketing campaigns
5. [ ] Analyze order fulfillment times

---

Generated: Test Data Setup & Verification Guide
