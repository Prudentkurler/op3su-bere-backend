#!/usr/bin/env python
"""
Azure App Service startup script for Django application.
This script handles database migrations and static file collection.
"""

import os
import sys
import subprocess

def run_command(command):
    """Run a shell command and handle errors."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(f"STDOUT: {result.stdout}")
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        sys.exit(1)
    
    return result

def main():
    """Main startup sequence for Azure deployment."""
    print("Starting Azure App Service Django application...")
    
    # Collect static files
    print("Collecting static files...")
    run_command("python manage.py collectstatic --noinput")
    
    # Run database migrations
    print("Running database migrations...")
    run_command("python manage.py migrate --noinput")
    
    # Create superuser if environment variables are provided
    username = os.getenv('DJANGO_SUPERUSER_USERNAME')
    email = os.getenv('DJANGO_SUPERUSER_EMAIL')
    password = os.getenv('DJANGO_SUPERUSER_PASSWORD')
    
    if username and email and password:
        print("Creating Django superuser...")
        try:
            run_command("python manage.py createsuperuser --noinput")
        except:
            print("Superuser creation failed or user already exists")
    
    print("Startup completed successfully!")

if __name__ == "__main__":
    main()