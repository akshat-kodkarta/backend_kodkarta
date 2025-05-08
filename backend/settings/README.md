# Django Settings Configuration

This directory contains the different settings configurations for the Kodkarta backend application.

## Settings Files

- `base.py`: Contains common settings shared across all environments
- `local.py`: Settings for local development with minimal restrictions
- `development.py`: Settings for development environment
- `production.py`: Settings for production environment

## How to Use

### For Local Development

Run the server with:

```bash
python manage.py runserver --settings=backend.settings.local
```

### For Development Environment

Run the server with:

```bash
python manage.py runserver --settings=backend.settings.development
```

### For Production Environment

Run the server with:

```bash
python manage.py runserver --settings=backend.settings.production
```

## Environment Variables

Make sure you have the appropriate environment variables set in your `.env` file or environment. The main settings file loads variables from `.env` at the root of the project.

## Troubleshooting

If you get HTTP 400 errors, check that your `ALLOWED_HOSTS` is correctly configured for the environment you're running in. For local development, you should use `local.py` which allows all hosts. 