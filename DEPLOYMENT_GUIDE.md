# Deployment & Setup Guide for Advanced Features

## Local Development Setup

### Prerequisites
- Python 3.8+
- pip package manager
- Git (for version control)
- SQLite3 (included with Python)

### Step 1: Apply Migrations
```bash
# Create migration files for new models
python manage.py makemigrations customer_app

# Apply migrations to database
python manage.py migrate
```

### Step 2: Create Super Admin User (if not exists)
```bash
python manage.py createsuperuser
```

### Step 3: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 4: Run Development Server
```bash
# Run on http://localhost:8000
python manage.py runserver
```

### Step 5: Test the Features
1. Go to http://localhost:8000/admin/
2. Login with admin credentials
3. Navigate to "PromoCode" section
4. Create a test promo code:
   - Code: SAVE10
   - Discount: 10%
   - Min Order Amount: 100
   - Valid From: Today
   - Valid Until: 30 days from now
   - Active: ✓

5. Test as customer:
   - Browse menu and add items
   - Go to checkout
   - Enter promo code "SAVE10"
   - Verify discount is applied

---

## Deployment to Render (Production)

### Step 1: Push Changes to GitHub
```bash
git add .
git commit -m "Add advanced features: reviews, promo codes, order tracking"
git push origin main
```

### Step 2: Render Auto-Deployment
- Render will automatically detect the push
- Build will trigger with `build.sh` script
- Migrations will run automatically
- App will be redeployed

### Step 3: Verify on Production
1. Go to your Render URL (e.g., https://restaurant-app.onrender.com)
2. Login as customer
3. Complete a test order with promo code
4. View order details page

---

## Database Backup (Important!)

Before deploying, backup your database:

```bash
# On local machine
cp db.sqlite3 db.sqlite3.backup

# Push backup to repository (optional)
git add db.sqlite3.backup
git commit -m "Database backup before advanced features"
git push origin main
```

---

## Troubleshooting

### Issue: Migration Errors
```bash
# Reset migrations (development only - DESTROYS DATA)
python manage.py migrate customer_app zero
python manage.py makemigrations customer_app
python manage.py migrate customer_app
```

### Issue: Static Files Not Loading
```bash
# Recollect static files
python manage.py collectstatic --clear --noinput
```

### Issue: Admin Panel Errors
```bash
# Check for system errors
python manage.py check
```

### Issue: Promo Code Not Applying
- Verify promo code date range in admin panel
- Check `is_active` flag is enabled
- Verify usage count hasn't exceeded limit
- Check minimum order amount condition

---

## Admin Panel Guide

### Managing Promo Codes
1. Go to Admin → PromoCode
2. Click "Add Promo Code"
3. Fill in details:
   - **Code**: Unique code customers enter (e.g., "SAVE10")
   - **Discount Percent**: 1-100 (e.g., 10 for 10% off)
   - **Max Discount Amount**: Optional cap (e.g., ₹500 max)
   - **Min Order Amount**: Minimum order to use (e.g., ₹100)
   - **Valid From/Until**: Date range for active period
   - **Usage Limit**: Optional max uses (e.g., 100)
4. Check "Is Active" to enable
5. Click "Save"

### Viewing Order Reviews
1. Go to Admin → Reviews
2. Filter by rating or date
3. See customer comments
4. Use for improving service

### Tracking Order Status Changes
1. Go to Admin → Order Status History
2. See who changed status and when
3. Filter by status or date
4. View optional notes on changes

---

## Security Considerations

1. **Promo Code Validation**:
   - All validation happens server-side
   - Client cannot manipulate discount amount
   - Usage limits are enforced

2. **Review Submission**:
   - Only authenticated customers can submit reviews
   - Customer must own the order to review it

3. **Order Details**:
   - Customers can only see their own order details
   - Status history is read-only for customers

---

## Performance Optimization

### Database Indexes (Already Applied)
- Promo codes are indexed by code (unique)
- Reviews are indexed by order and customer
- Status history is indexed by order

### Query Optimization (Already Applied)
- `prefetch_related()` for status history in order detail view
- `filter()` to reduce database queries

---

## Monitoring & Analytics

### Key Metrics to Track
1. **Promo Code Usage**:
   - Most used codes
   - Total discount given
   - Conversion rate improvement

2. **Customer Reviews**:
   - Average rating
   - Review frequency
   - Common feedback themes

3. **Order Status**:
   - Average time per status
   - Completion rate
   - Cancellation rate

---

## Future Maintenance Tasks

### Weekly
- Check unused promo codes and deactivate
- Review negative ratings and address issues

### Monthly
- Analyze promo code effectiveness
- Review order processing times
- Check database backup status

### Quarterly
- Create new promo campaigns
- Analyze customer feedback trends
- Optimize database performance

---

## Quick Commands Reference

```bash
# Development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# System check
python manage.py check

# Shell (Python interactive)
python manage.py shell

# Clear cache
python manage.py clear_cache

# Database backup
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d)
```

---

## Support & Documentation

For more information:
- Django Docs: https://docs.djangoproject.com/
- Bootstrap Docs: https://getbootstrap.com/docs/
- Project GitHub: [Your Repository URL]

---

Last Updated: Advanced Features Phase
