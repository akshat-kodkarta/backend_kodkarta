# Django Project Setup Guide

## Installation & Setup

Ensure you have a Django project set up with the required apps and migration scripts placed inside the `apps` directory.

## Project Structure

```dir
project_root/
├── manage.py
├── requirements.txt
│
├── config/                
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py                 # Main URL routing
│   ├── asgi.py
│   └── wsgi.py
│
└── apps/               
    ├── users/                      # User app
    │   ├── __init__.py
    │   ├── models/                # Models directory
    │   │   ├── __init__.py
    │   │   ├── user.py           # User model definitions
    │   │   └── profile.py        # Profile model definitions
    │   ├── views/                # Views directory
    │   │   ├── __init__.py
    │   │   ├── auth_views.py     # Authentication views
    │   │   └── user_views.py     # User management views
    │   ├── services.py            # Business logic
    │   ├── serializers.py         # DRF serializers
    │   ├── urls.py               
    │   ├── admin.py
    │   ├── apps.py
    │   └── tests.py
    ├── github_app/                # GitHub integration app
    │   ├── __init__.py
    │   ├── models/                # Models directory
    │   │   ├── __init__.py
    │   │   └── github_models.py   # GitHub data models
    │   ├── views/                # Views directory
    │   │   ├── __init__.py
    │   │   └── github_views.py    # GitHub API views
    │   ├── services.py            # GitHub API integration services
    │   ├── serializers.py         # DRF serializers
    │   ├── urls.py                # GitHub API endpoints
    │   ├── admin.py
    │   ├── apps.py
    │   └── tests.py
    └── second_app/               # Timeslots Data app
        ├── __init__.py
        ├── models/               # Models directory
        │   ├── __init__.py
        │   ├── timeslot.py      # Timeslot model definitions
        │   └── booking.py       # Booking model definitions
        ├── views/               # Views directory
        │   ├── __init__.py
        │   ├── timeslot_views.py # Timeslot views
        │   └── booking_views.py  # Booking views
        ├── services.py           # Business logic
        ├── serializers.py        # DRF serializers
        ├── urls.py
        ├── admin.py
        ├── apps.py
        └── tests.py
```

## Environment Setup

Follow these steps to set up your development environment:

### 1. Activate Virtual Environment
```sh
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate  # On Windows
```

### 2. Create a New Django App
```sh
python manage.py startapp github_app
```
This command creates a new Django app with the standard structure including views.py, models.py, etc. Initially, this creates the app in the project root with the basic Django app structure.

### 3. Move the App to the apps Directory
```sh
mv github_app apps/
```
Following our project structure, all apps should be placed inside the 'apps' directory to maintain organizational consistency. This ensures all apps are in the same location for better project organization.

### 4. Restructure the App for Modularity
After moving the app to the apps directory, you should restructure it to match our modular approach:

1. Create models directory:
```sh
mkdir apps/github_app/models
touch apps/github_app/models/__init__.py
touch apps/github_app/models/github_models.py
```

2. Create views directory:
```sh
mkdir apps/github_app/views
touch apps/github_app/views/__init__.py
touch apps/github_app/views/github_views.py
```

### 5. Get the `.env` File
Ask the developer for the environment file located at:
```
mindpsy/env/.env_dev
```
Place this file in the appropriate directory before proceeding.

### 6. Install Dependencies
```sh
pip install -r mindpsy/requirements/base.txt
```

### 7. Register Your App
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
    'apps.github_app',  # Add your new app here
]
```

### 8. Run Migrations
```sh
python manage.py makemigrations
python manage.py migrate
```

### 9. Start Development Server
```sh
python manage.py runserver
``` 