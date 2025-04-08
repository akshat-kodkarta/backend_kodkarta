# Django Project Setup Guide

## Overview

This guide provides instructions for setting up a modular Django project with a clear separation of concerns and standardized directory structure.

## Project Structure

```dir
project_root/
├── manage.py                    # Django management script
├── requirements.txt             # Project dependencies
│
├── config/                      # Project configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              # Base settings
│   │   ├── local.py             # Local development settings
│   │   └── production.py        # Production settings
│   ├── urls.py                  # Main URL routing
│   ├── asgi.py                  # ASGI configuration
│   └── wsgi.py                  # WSGI configuration
│
└── apps/                        # All Django applications
    ├── users/                   # User management app
    │   ├── __init__.py
    │   ├── models/              # Models directory
    │   │   ├── __init__.py
    │   │   ├── user.py          # User model definitions
    │   │   └── profile.py       # Profile model definitions
    │   ├── views/               # Views directory
    │   │   ├── __init__.py
    │   │   ├── auth_views.py    # Authentication views
    │   │   └── user_views.py    # User management views
    │   ├── services.py          # Business logic
    │   ├── serializers.py       # DRF serializers
    │   ├── urls.py              # App-specific URLs
    │   ├── admin.py             # Admin configuration
    │   ├── apps.py              # App configuration
    │   └── tests.py             # Tests
    ├── github_app/              # GitHub integration app
    │   ├── __init__.py
    │   ├── models/              # Models directory
    │   │   ├── __init__.py
    │   │   └── github_models.py # GitHub data models
    │   ├── views/               # Views directory
    │   │   ├── __init__.py
    │   │   └── github_views.py  # GitHub API views
    │   ├── services.py          # GitHub API integration services
    │   ├── serializers.py       # DRF serializers
    │   ├── urls.py              # GitHub API endpoints
    │   ├── admin.py             # Admin configuration
    │   ├── apps.py              # App configuration
    │   └── tests.py             # Tests
    └── second_app/              # Another app example
        ├── __init__.py
        ├── models/              # Models directory
        │   ├── __init__.py
        │   ├── timeslot.py      # Timeslot model definitions
        │   └── booking.py       # Booking model definitions
        ├── views/               # Views directory
        │   ├── __init__.py
        │   ├── timeslot_views.py # Timeslot views
        │   └── booking_views.py  # Booking views
        ├── services.py          # Business logic
        ├── serializers.py       # DRF serializers
        ├── urls.py              # App-specific URLs
        ├── admin.py             # Admin configuration
        ├── apps.py              # App configuration
        └── tests.py             # Tests
```

## Initial Setup

Follow these steps to set up your development environment:

### 1. Activate Virtual Environment
```sh
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```

### 2. Get the `.env` File
```sh
# Request the environment file from the development team
# Place it in the appropriate directory:
cp /path/to/received/.env_dev mindpsy/env/.env_dev
```

### 3. Install Dependencies
```sh
pip install -r mindpsy/requirements/base.txt
```

## Creating a New App

To add a new app to your Django project, follow these steps:

### 1. Create and Position the App
```sh
# Create the app with Django's startapp command
python manage.py startapp your_new_app_name

# Move the app to the apps directory
mv your_new_app_name apps/
```

### 2. Restructure for Modularity
```sh
# Create models directory
mkdir apps/your_new_app_name/models
touch apps/your_new_app_name/models/__init__.py

# Create views directory
mkdir apps/your_new_app_name/views
touch apps/your_new_app_name/views/__init__.py

# Move the original models.py content to a specific model file
mv apps/your_new_app_name/models.py apps/your_new_app_name/models/temp.py
touch apps/your_new_app_name/models/your_model_name.py
# Copy content from temp.py to your_model_name.py, then remove temp
rm apps/your_new_app_name/models/temp.py

# Move the original views.py content to a specific view file
mv apps/your_new_app_name/views.py apps/your_new_app_name/views/temp.py
touch apps/your_new_app_name/views/your_view_name.py
# Copy content from temp.py to your_view_name.py, then remove temp
rm apps/your_new_app_name/views/temp.py
```

### 3. Configure Module Imports
Update the __init__.py files to make your modules accessible at the package level:

models/__init__.py:
```python
from .your_model_name import *
```

views/__init__.py:
```python
from .your_view_name import *
```

### 4. Register Your App
Add your new app to the INSTALLED_APPS list in config/settings/base.py:

```python
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    # ...
    
    # Local apps
    'apps.users',
    'apps.second_app',
    'apps.your_new_app_name',  # Add your new app here
]
```

### 5. Include URLs
Update the main urls.py to include your app's URLs:

```python
from django.urls import path, include

urlpatterns = [
    # ...existing patterns...
    path('your-endpoint/', include('apps.your_new_app_name.urls')),
]
```

### 6. Run Migrations
```sh
python manage.py makemigrations
python manage.py migrate
```

### 7. Start Development Server
```sh
python manage.py runserver
```

## Example: Creating the GitHub App

Here's an example of how we created the github_app:

```sh
# 1. Create the app
python manage.py startapp github_app

# 2. Move to apps directory
mv github_app apps/

# 3. Create modular structure
mkdir apps/github_app/models
mkdir apps/github_app/views
touch apps/github_app/models/__init__.py
touch apps/github_app/views/__init__.py
touch apps/github_app/models/github_models.py
touch apps/github_app/views/github_views.py

# 4. Register in INSTALLED_APPS
# Edit config/settings/base.py to add 'apps.github_app'

# 5. Run migrations
python manage.py makemigrations
python manage.py migrate
``` 