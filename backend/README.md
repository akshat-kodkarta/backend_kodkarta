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



No, you do NOT need two VMs to serve multiple subdomains like:

dashboard.kodkarta.io → Next.js frontend

api.kodkarta.io → Django backend

You can absolutely do this with one VM and one IP address using Nginx as a reverse proxy. The trick is to use virtual hosts in your Nginx config to route traffic based on the subdomain.

✅ How It Works (One VM, One IP, Multiple Subdomains)
When a request hits your public IP (e.g., 20.50.12.34), Nginx looks at the Host header to decide where to route it:

If host is dashboard.kodkarta.io, Nginx forwards to Next.js running on, say, localhost:3000

If host is api.kodkarta.io, Nginx forwards to Django running on localhost:8000

🔧 Nginx Sample Config
nginx
Copy
Edit
# /etc/nginx/sites-available/dashboard.kodkarta.io
server {
    listen 80;
    server_name dashboard.kodkarta.io;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# /etc/nginx/sites-available/api.kodkarta.io
server {
    listen 80;
    server_name api.kodkarta.io;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
Then symlink them to sites-enabled:

bash
Copy
Edit
ln -s /etc/nginx/sites-available/dashboard.kodkarta.io /etc/nginx/sites-enabled/
ln -s /etc/nginx/sites-available/api.kodkarta.io /etc/nginx/sites-enabled/
Restart Nginx:

bash
Copy
Edit
sudo systemctl restart nginx
🌐 DNS Configuration
At your domain registrar (e.g., GoDaddy, Namecheap, Cloudflare), add A records:

Subdomain	Type	Value
dashboard.kodkarta.io	A	<your VM IP>
api.kodkarta.io	A	<your VM IP>

🔒 Bonus: Use Let's Encrypt for HTTPS
Use Certbot to secure both domains:

bash
Copy
Edit
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d dashboard.kodkarta.io -d api.kodkarta.io
✅ Summary
One VM, one IP = no problem

Use Nginx with virtual host configs

Set proper DNS A records

No need for multiple VMs unless scaling or isolation is needed




| App Name        | Responsibility                                                          |
| --------------- | ----------------------------------------------------------------------- |
| `users`         | Auth, roles (admin, developer, etc.), GitHub/Azure login                |
| `products`      | User-defined "products" (units of software being monitored)             |
| `integrations`  | GitHub & Azure integration logic, storing repo/project metadata         |
| `assets`        | Discovered software components, cloud services, AI-generated code, etc. |
| `policies`      | Security/compliance policy definitions & rule evaluation logic          |
| `insights`      | AI-generated insights, anomaly detection, summaries, and RAG responses  |
| `visualization` | Asset graph generation, graph API, and frontend-related endpoints       |
