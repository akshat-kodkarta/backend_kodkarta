#!/usr/bin/env python
import os
import sys
import django
import psycopg2
import argparse

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def clear_migrations():
    # Set up Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.base')
    django.setup()

    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM django_migrations;")
            print("Migration history cleared successfully.")
    except Exception as e:
        print(f"Error clearing migrations: {e}")

def reset_database():
    # Get database settings from Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.base')
    django.setup()
    
    from django.conf import settings
    
    # Get database settings
    try:
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        breakpoint()
        # Safety check - prevent dropping system databases
        # if db_name.lower() in ('postgres', 'template0', 'template1'):
        #     print(f"ERROR: Cannot drop system database '{db_name}'")
        #     print("Check your settings - the database name appears to be set to a PostgreSQL system database.")
        #     return
            
        db_user = db_settings['USER']
        db_password = db_settings.get('PASSWORD', '')
        db_host = db_settings.get('HOST', 'localhost')
        db_port = db_settings.get('PORT', '5432')
        
        print(f"Database settings from Django:")
        print(f"  Database: {db_name}")
        print(f"  User: {db_user}")
        print(f"  Host: {db_host}")
        print(f"  Port: {db_port}")
        
    except (KeyError, AttributeError) as e:
        print(f"Error accessing database settings: {e}")
        print("Please check your Django settings configuration.")
        return
    
    # Connect to postgres database to be able to drop and create the target database
    conn_string = f"dbname='postgres' user='{db_user}'"
    if db_password:
        conn_string += f" password='{db_password}'"
    conn_string += f" host='{db_host}' port='{db_port}'"
    
    try:
        print(f"Connecting to postgres database to drop and recreate '{db_name}'...")
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            # Check for existing connections
            cursor.execute(f"""
                SELECT COUNT(*) FROM pg_stat_activity 
                WHERE datname = '{db_name}' 
                AND pid <> pg_backend_pid();
            """)
            active_connections = cursor.fetchone()[0]
            
            if active_connections > 0:
                print(f"There are {active_connections} active connections to the database.")
                # Try to terminate them, but don't fail if we can't
                try:
                    cursor.execute(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{db_name}'
                        AND pid <> pg_backend_pid();
                    """)
                    print("Terminated existing connections.")
                except Exception as e:
                    print(f"Warning: Could not terminate all connections: {e}")
                    print("Continuing with database drop anyway...")
            
            # Drop the database if it exists
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name};")
            print(f"Database '{db_name}' dropped.")
            
            # Create the database
            cursor.execute(f"CREATE DATABASE {db_name} WITH OWNER = {db_user};")
            print(f"Database '{db_name}' recreated.")
        
        conn.close()
        print("Database reset complete. You can now run migrations to create fresh tables.")
    except Exception as e:
        print(f"Error resetting database: {e}")
        print("If you don't have sufficient privileges, you may need to:")
        print("1. Connect to PostgreSQL as a superuser")
        print("2. Manually drop and recreate the database:")
        print(f"   DROP DATABASE IF EXISTS {db_name};")
        print(f"   CREATE DATABASE {db_name} WITH OWNER = {db_user};")

def list_databases():
    # Get database settings from Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.base')
    django.setup()
    
    from django.conf import settings
    
    try:
        db_settings = settings.DATABASES['default']
        db_user = db_settings['USER']
        db_password = db_settings.get('PASSWORD', '')
        db_host = db_settings.get('HOST', 'localhost')
        db_port = db_settings.get('PORT', '5432')
        
        # Connect to postgres database
        conn_string = f"dbname='postgres' user='{db_user}'"
        if db_password:
            conn_string += f" password='{db_password}'"
        conn_string += f" host='{db_host}' port='{db_port}'"
        
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;")
            databases = cursor.fetchall()
            
            print("Available databases:")
            for db in databases:
                print(f"  - {db[0]}")
        
        conn.close()
    except Exception as e:
        print(f"Error listing databases: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database migration management")
    parser.add_argument('--reset-db', action='store_true', help='Drop and recreate the database (DANGER: all data will be lost)')
    parser.add_argument('--clear-migrations', action='store_true', help='Clear the django_migrations table only')
    parser.add_argument('--list-dbs', action='store_true', help='List available databases')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts (use with caution)')
    
    args = parser.parse_args()
    
    if args.list_dbs:
        list_databases()
    elif args.reset_db:
        if args.force:
            reset_database()
        else:
            confirm = input("WARNING: This will DELETE ALL DATA in the database. Are you sure? (type 'yes' to confirm): ")
            if confirm.lower() == 'yes':
                reset_database()
            else:
                print("Database reset cancelled.")
    elif args.clear_migrations:
        clear_migrations()
    else:
        print("Please specify an action: --reset-db, --clear-migrations, or --list-dbs")
        print("Examples:")
        print("  python clear_migrations.py --clear-migrations")
        print("  python clear_migrations.py --reset-db")
        print("  python clear_migrations.py --list-dbs")
        print("Use --force to skip confirmation prompts (e.g., python clear_migrations.py --reset-db --force)") 