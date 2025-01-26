#!/bin/bash

set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Collect static files for Django
python manage.py collectstatic --noinput

# Run database migrations (optional, if using a database)
python manage.py migrate
