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




to remove all the migrations

find kodkartaBE/backend/apps/*/migrations -name "*.py" ! -name "__init__.py" -delete



# GitHub Repository Explorer

## Overview

GitHub Repository Explorer is a web application that allows users to analyze and visualize GitHub repositories. It provides insights into repository structure, branches, contributors, and file relationships through an interactive visualization.

## Features

- **Repository Analysis**: Explore any public GitHub repository by providing its URL
- **Branch Visualization**: View all branches and their relationships
- **Contributor Insights**: See who contributed to each branch
- **File Structure**: Browse files within each branch
- **Interactive Map**: Visual representation of repository components and their relationships
- **Rate Limit Management**: Smart handling of GitHub API rate limits

## How It Works

### Authentication

The application requires a GitHub Personal Access Token to authenticate API requests. This increases the rate limit from 60 requests/hour (unauthenticated) to 5,000 requests/hour (authenticated).

### Repository Exploration Process

1. **Initial Request**: When a user submits a repository URL and GitHub token, the application sends a request to the backend.

2. **Asynchronous Processing**: The backend processes the request asynchronously to avoid blocking the UI:
   - Fetches repository metadata
   - Retrieves branches and their details
   - Collects contributor information
   - Analyzes file structure

3. **Hierarchical Scanning**:
   - First level: Organization and repositories
   - Second level: Repository structure and branches
   - Third level: Files, code, and dependencies
   - Fourth level: Detailed code analysis and secrets scanning

4. **Rate Limit Management**:
   - Tracks remaining API requests
   - Implements intelligent backoff strategy when approaching limits
   - Prioritizes critical requests over less important ones
   - Caches results to minimize duplicate requests

5. **Visualization**:
   - Creates an interactive D3.js visualization of the repository
   - Displays branches as nodes connected to the main repository
   - Shows contributors connected to their respective branches
   - Provides a file browser for exploring repository contents

### Technical Implementation

#### Frontend

- **HTML/CSS/JavaScript**: Responsive UI with modern design principles
- **Bootstrap**: For layout and basic components
- **D3.js**: For interactive repository visualization
- **Fetch API**: For asynchronous communication with the backend

#### Backend

- **Python/Flask**: Server-side processing and API handling
- **PyGithub**: GitHub API client for Python
- **Asynchronous Processing**: Background tasks for handling long-running operations
- **Caching**: Stores results to minimize API calls

## Detailed Setup Guide

### Prerequisites

- Python 3.8 or higher
- Git
- Internet connection
- GitHub account (for creating a Personal Access Token)

### Step 1: Clone the Repository

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies

The project requires several Python packages. Install them using pip:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file contains:

```
# Web Framework
flask==2.0.1
flask-cors==3.0.10

# GitHub Interaction
PyGithub==1.55
requests==2.26.0

# Environment Management
python-dotenv==0.19.0

# Data Processing
pyyaml==6.0
typing-extensions==4.5.0

# Optional: For advanced async processing
asyncio==3.4.3

# Optional: For logging
logging==0.5.1.2
```

### Step 3: Create a GitHub Personal Access Token

1. Log in to your GitHub account
2. Go to **Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**
3. Click **Generate new token** > **Generate new token (classic)**
4. Give your token a descriptive name (e.g., "Repository Explorer")
5. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read-only access to organization membership)
   - `user:email` (Access user email addresses)
6. Click **Generate token**
7. **IMPORTANT**: Copy your token immediately and store it securely. GitHub will only show it once!

### Step 4: Run the Application

```bash
python app.py
```

The application will start and be available at `http://localhost:5000` in your web browser.

### Step 5: Using the Application

1. Open your web browser and navigate to `http://localhost:5000`
2. You'll see the GitHub Repository Explorer interface with two input fields:
   - **GitHub Repository URL**: Enter the full URL of the repository you want to explore (e.g., `https://github.com/facebook/react`)
   - **GitHub Personal Access Token**: Paste your GitHub token here

3. Click the **Explore Repository** button to start the analysis
4. The application will:
   - Connect to GitHub using your token
   - Fetch repository data
   - Process the information
   - Display the results in the visualization panel

5. Once loaded, you can:
   - View the repository structure
   - Click on branches to see their files
   - Explore contributor information
   - Navigate through the file structure
   - View the relationships between different components

### Troubleshooting

- **Rate Limit Exceeded**: If you see this error, wait for your rate limit to reset (usually 1 hour) or use a different token
- **Repository Not Found**: Verify the repository URL is correct and publicly accessible
- **Token Authentication Failed**: Ensure your token is valid and has the required permissions
- **Application Not Starting**: Check that all dependencies are installed correctly

## Rate Limit Handling

The application implements a sophisticated approach to handle GitHub API rate limits:

1. **Prioritized Scanning**: Critical paths are scanned first, with less important data fetched later
2. **Backoff Strategy**: When rate limits are approached, the application implements exponential backoff
3. **Hierarchical Processing**: Data is processed based on hierarchy level:
   - Level 1: Organization and repositories (minimal API calls)
   - Level 2: Repository structure and branches (moderate API calls)
   - Level 3: Files and code (higher API usage)
   - Level 4: Detailed analysis (highest API usage)
4. **Background Processing**: Lower priority scans happen asynchronously in the background
5. **Rate Limit Monitoring**: Continuous tracking of remaining API requests

## Usage Guidelines

1. **Use a Personal Access Token**: Always use a GitHub token to increase your rate limit
2. **Start with Smaller Repositories**: Large repositories like React or TensorFlow have thousands of files and will quickly exhaust rate limits
3. **Explore Incrementally**: Start with high-level exploration before diving into specific branches
4. **Be Patient with Large Repositories**: The application implements backoff when rate limits are hit

## Future Improvements

- Implement persistent caching to further reduce API calls
- Add repository comparison features
- Enhance visualization with more metrics and insights
- Implement webhook support for real-time updates
- Add support for organization-wide analysis

## Technical Requirements

- Modern web browser with JavaScript enabled
- GitHub Personal Access Token with appropriate permissions
- Internet connection to access GitHub API

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.





Server connection: ssh -i ~/.ssh/dev-server_key.pem azureuser@135.225.105.47


sites-available/mindPsy_backend /etc/nginx/sit