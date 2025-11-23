#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --noinput

# Collect static files - THIS IS CRUCIAL FOR CSS/JS TO WORK!
python manage.py collectstatic --noinput --clear

