# API Documentation - Advanced Features

## Overview
This document provides detailed API documentation for all new AJAX endpoints and backend features.

---

## 1. Promo Code API

### Apply Promo Code
**Endpoint**: `/customer/promo/apply/`  
**Method**: `POST`  
**Authentication**: Optional (works with or without login)  
**Content-Type**: `application/x-www-form-urlencoded`

#### Request Parameters
```
code: string (required) - The promo code to apply (case-insensitive)
```

#### Request Example (JavaScript)
```javascript
fetch('/customer/promo/apply/', {
  method: 'POST',
  headers: {
    'X-CSRFToken': csrfToken,
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: 'code=SAVE10'
})
.then(response => response.json())
.then(data => console.log(data));
```

#### Success Response (200)
```json
{
  "status": "success",
  "message": "Promo code 'SAVE10' applied successfully!",
  "discount_amount": 100.50,
  "discount_percent": 10,
  "original_amount": 1005.00,
  "final_amount": 904.50
}
```

#### Error Responses

**Code Not Found (400)**
```json
{
  "status": "error",
  "message": "Promo code not found"
}
```

**Code Expired (400)**
```json
{
  "status": "error",
  "message": "Promo code has expired"
}
```

**Code Inactive (400)**
```json
{
  "status": "error",
  "message": "Promo code is not active"
}
```

**Usage Limit Exceeded (400)**
```json
{
  "status": "error",
  "message": "Promo code usage limit exceeded"
}
```

**Minimum Order Amount Not Met (400)**
```json
{
  "status": "error",
  "message": "Minimum order amount required: ₹500.00"
}
```

#### Implementation Details
- Promo code is stored in `request.session['promo_code']` after successful validation
- Discount persists across requests via session
- All validation happens server-side (cannot be bypassed by client)
- Usage count is incremented on each successful application

---

## 2. Review API

### Submit Order Review
**Endpoint**: `/customer/review/<order_id>/`  
**Method**: `POST`  
**Authentication**: Required (user must be logged in)  
**Content-Type**: `application/x-www-form-urlencoded`

#### URL Parameters
```
order_id: string (required) - The unique order ID
```

#### Request Parameters
```
rating: int (required) - Rating from 1-5
comment: string (optional) - Customer's feedback/comment
```

#### Request Example (HTML Form)
```html
<form method="post" action="/customer/review/order-uuid-here/">
  {% csrf_token %}
  <select name="rating" required>
    <option value="5">5 Stars - Excellent</option>
    <option value="4">4 Stars - Good</option>
    <option value="3">3 Stars - Average</option>
    <option value="2">2 Stars - Poor</option>
    <option value="1">1 Star - Very Poor</option>
  </select>
  <textarea name="comment" rows="3"></textarea>
  <button type="submit">Submit Review</button>
</form>
```

#### Success Response
- Redirects to `/customer/orders/` with success message:
```
"Review submitted successfully!"
```

#### Error Responses

**Not Authenticated (302 Redirect)**
```
Redirects to: /customer/user_log/
```

**Invalid Rating (Redirect)**
```
Message: "Rating is required"
Redirects to: /customer/orders/
```

**Order Not Found (404)**
```
HTTP 404 - Order not found
```

#### Implementation Details
- Review is created or updated (idempotent - can re-submit to update)
- Customers can only review their own orders
- Reviews are optional - submitted via POST to dedicated endpoint
- Existing reviews are updated if customer submits again

---

## 3. Order Details API (Page)

### Get Order Details
**Endpoint**: `/customer/order/<order_id>/`  
**Method**: `GET`  
**Authentication**: Required (customer must own the order)  
**Response**: HTML page with order information

#### URL Parameters
```
order_id: string (required) - The unique order ID
```

#### Response Contains
- Order information (ID, date, total amount)
- Order items with quantities and prices
- Delivery details
- Status timeline (all historical status changes)
- Review form (if not yet reviewed)
- Existing review (if already reviewed)

#### Error Responses

**Not Authenticated (302 Redirect)**
```
Redirects to: /customer/user_log/
Message: "Please login to view order details."
```

**Order Not Found (404)**
```
HTTP 404 - Order not found
```

**Unauthorized Access (404)**
```
Returns 404 if customer tries to view another customer's order
```

---

## Database Models

### Review Model
```python
class Review(models.Model):
    RATING_CHOICES = [(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)]
    
    customer = ForeignKey(regdb)
    order = ForeignKey(Order, related_name='reviews')
    food_item = ForeignKey(fooditems, null=True, blank=True)
    rating = IntegerField(choices=RATING_CHOICES)
    comment = TextField(blank=True, null=True)
    created_at = DateTimeField(auto_now_add=True)
```

### PromoCode Model
```python
class PromoCode(models.Model):
    code = CharField(max_length=50, unique=True)
    discount_percent = IntegerField()
    max_discount_amount = DecimalField(null=True, blank=True)
    min_order_amount = DecimalField(default=0)
    is_active = BooleanField(default=True)
    valid_from = DateTimeField()
    valid_until = DateTimeField()
    usage_limit = IntegerField(null=True, blank=True)
    usage_count = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
```

### OrderStatusHistory Model
```python
class OrderStatusHistory(models.Model):
    order = ForeignKey(Order, related_name='status_history')
    status = CharField(choices=ORDER_STATUS_CHOICES)
    changed_at = DateTimeField(auto_now_add=True)
    updated_by = CharField(max_length=100, null=True, blank=True)
    note = TextField(blank=True, null=True)
```

---

## Validation Rules

### Promo Code Validation
1. Code must exist in database
2. Code must be marked as active (`is_active=True`)
3. Current time must be between `valid_from` and `valid_until`
4. Order amount must be >= `min_order_amount`
5. Usage count must not exceed `usage_limit` (if set)

### Review Validation
1. User must be authenticated
2. Rating must be integer between 1-5
3. User must own the order
4. Comment is optional

### Discount Calculation
```
discount_amount = (order_amount * discount_percent) / 100
if max_discount_amount is set:
    discount_amount = min(discount_amount, max_discount_amount)
final_amount = order_amount - discount_amount
```

---

## Session Variables

### Promo Code
```
request.session['promo_code'] = 'SAVE10'
```
Stored after successful promo application, persists across requests.

### Cart (Existing)
```
request.session['cart'] = {'123': 2, '456': 1}  # {item_id: quantity}
```

### Favorites (Existing)
```
request.session['favorites'] = [123, 456, 789]  # list of item IDs
```

---

## HTTP Status Codes

| Status | Meaning | Scenario |
|--------|---------|----------|
| 200 | OK | Successful promo code validation |
| 302 | Redirect | Authentication required |
| 400 | Bad Request | Invalid promo code or parameters |
| 404 | Not Found | Order or resource not found |
| 500 | Server Error | Unexpected error |

---

## Rate Limiting

Currently: No rate limiting implemented

**Recommended for future**:
- Limit promo code application attempts to 5 per minute
- Limit review submissions to 1 per order
- Add CAPTCHA for abuse prevention

---

## Security Considerations

### CSRF Protection
All POST endpoints require CSRF token:
```javascript
headers: {
  'X-CSRFToken': '{{ csrf_token }}'
}
```

### Input Validation
- Rating must be integer 1-5
- Comment length limited by database (TextField)
- Promo code lookup is case-insensitive but stored uppercase

### Authorization
- Customers can only see their own orders
- Customers can only submit reviews for their orders
- Admin can see all data via admin panel

---

## Examples

### Example 1: Apply Promo Code in Checkout
```javascript
// HTML
<input type="text" id="promo_code" placeholder="Enter promo code">
<button id="apply_btn">Apply</button>
<div id="discount_display"></div>

// JavaScript
document.getElementById('apply_btn').addEventListener('click', async () => {
  const code = document.getElementById('promo_code').value;
  
  const response = await fetch('/customer/promo/apply/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: `code=${encodeURIComponent(code)}`
  });
  
  const data = await response.json();
  
  if (data.status === 'success') {
    document.getElementById('discount_display').innerHTML = 
      `Saved: ₹${data.discount_amount.toFixed(2)}`;
  } else {
    alert(data.message);
  }
});
```

### Example 2: Submit Review via AJAX
```javascript
document.getElementById('review_form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = new FormData(e.target);
  const orderId = '{{ order.order_id }}';
  
  const response = await fetch(`/customer/review/${orderId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: formData
  });
  
  if (response.ok) {
    alert('Review submitted successfully!');
    location.reload();
  }
});
```

---

## Troubleshooting

### Promo Code Returns "Not Found"
- Check spelling in admin panel
- Verify code is marked active
- Check date range validity
- Confirm minimum order amount is met

### Review Not Submitted
- Ensure user is logged in
- Check that order belongs to logged-in customer
- Verify rating is selected (1-5)
- Check browser console for errors

### Status History Not Updating
- Admin/waiter must change order status in admin panel
- Refresh order detail page to see updates
- Check database for OrderStatusHistory records

---

## Future API Endpoints (Planned)

- `POST /customer/order/<order_id>/status/` - Update order status (admin only)
- `GET /customer/orders/feed/` - Get order tracking feed
- `POST /customer/review/<review_id>/delete/` - Delete review
- `GET /customer/promo/list/` - Get available promo codes

---

Generated: Advanced Features API Documentation
