# Render Deployment Guide

## Static Files Configuration

Your Django project is now configured to serve static files (CSS, JS, Images) on Render using WhiteNoise.

## Render Configuration Steps

### 1. Build Command
In your Render service settings, set the **Build Command** to:
```bash
bash build.sh
```

Or if Render doesn't support build.sh, set it to:
```bash
pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear
```

### 2. Start Command
Set the **Start Command** to:
```bash
gunicorn restaurant.wsgi:application
```

### 3. Environment Variables (Optional)
If you need to set environment variables, add them in Render's Environment tab:
- `SECRET_KEY` (if you want to override the default)
- `DEBUG=False` (already set in settings.py)
- `ALLOWED_HOSTS` (currently set to '*' which allows all hosts)

### 4. Static Files
The build script will automatically:
- Install all dependencies (including WhiteNoise)
- Run database migrations
- Collect all static files to the `staticfiles` directory

WhiteNoise middleware will serve these files automatically in production.

## What Was Changed

1. ✅ Added `whitenoise==6.8.2` to `requirements.txt`
2. ✅ Added WhiteNoise middleware to `settings.py` (right after SecurityMiddleware)
3. ✅ Configured `STATICFILES_STORAGE` to use WhiteNoise
4. ✅ Created `build.sh` script to run collectstatic during deployment
5. ✅ Updated static files configuration for production

## Troubleshooting

If CSS/JS still doesn't load after deployment:

1. **Check Render Build Logs**: Ensure `collectstatic` ran successfully
2. **Verify Static Files**: Check that files exist in `staticfiles/` directory
3. **Check WhiteNoise**: Ensure WhiteNoise middleware is enabled (it should be)
4. **Clear Cache**: Try hard refresh (Ctrl+F5) or clear browser cache
5. **Check Static URL**: Verify that templates use `{% static 'app_name/file.css' %}` correctly

## After Deployment

Once deployed, your static files will be served from:
- `/static/admin_app/...` - Admin app static files
- `/static/customer_app/...` - Customer app static files
- `/static/waiter_app/...` - Waiter app static files

All static files are automatically compressed and optimized by WhiteNoise.

