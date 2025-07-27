#!/usr/bin/env python3
"""
Configuration validation script for Miniflux to Instapaper webhook service

This script validates the configuration and tests connectivity to Instapaper.
"""

import os
import requests
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if .env file exists and load it"""
    if os.path.exists('.env'):
        load_dotenv()
        print("✅ .env file found and loaded")
        return True
    else:
        print("❌ .env file not found")
        print("   Please copy .env.sample to .env and configure your credentials")
        return False

def check_required_config():
    """Check required configuration variables"""
    issues = []

    # Check Instapaper username
    username = os.getenv('INSTAPAPER_USERNAME')
    if not username:
        issues.append("INSTAPAPER_USERNAME is not set")
    else:
        print(f"✅ Instapaper username: {username}")

    # Check webhook secret (recommended but not required)
    secret = os.getenv('MINIFLUX_WEBHOOK_SECRET')
    if not secret:
        print("⚠️  MINIFLUX_WEBHOOK_SECRET is not set (signature verification disabled)")
    else:
        print("✅ Webhook secret is configured")

    # Check optional password
    password = os.getenv('INSTAPAPER_PASSWORD', '')
    if password:
        print("✅ Instapaper password is set")
    else:
        print("ℹ️  Instapaper password is not set (this is normal if you don't have one)")

    return issues

def test_instapaper_connection():
    """Test connection to Instapaper API"""
    username = os.getenv('INSTAPAPER_USERNAME')
    password = os.getenv('INSTAPAPER_PASSWORD', '')

    if not username:
        print("❌ Cannot test Instapaper connection - username not configured")
        return False

    try:
        print("🔍 Testing Instapaper API connection...")

        response = requests.post(
            'https://www.instapaper.com/api/authenticate',
            data={
                'username': username,
                'password': password
            },
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Instapaper authentication successful")
            return True
        elif response.status_code == 403:
            print("❌ Instapaper authentication failed - invalid credentials")
            return False
        elif response.status_code == 500:
            print("⚠️  Instapaper service error - try again later")
            return False
        else:
            print(f"❌ Unexpected response from Instapaper: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to Instapaper: {e}")
        return False

def test_dependencies():
    """Test that all required Python packages are available"""
    try:
        import flask
        import requests
        import dotenv
        print("✅ All Python dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False

def main():
    print("=== Miniflux to Instapaper Configuration Validator ===")
    print()

    # Check dependencies
    print("1. Checking Python dependencies...")
    deps_ok = test_dependencies()
    print()

    if not deps_ok:
        print("Please install missing dependencies before continuing.")
        sys.exit(1)

    # Check environment file
    print("2. Checking configuration file...")
    env_ok = check_environment()
    print()

    if not env_ok:
        sys.exit(1)

    # Check required configuration
    print("3. Validating configuration...")
    issues = check_required_config()
    print()

    if issues:
        print("❌ Configuration issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print()
        sys.exit(1)

    # Test Instapaper connection
    print("4. Testing Instapaper connection...")
    instapaper_ok = test_instapaper_connection()
    print()

    # Summary
    print("=== Validation Summary ===")
    print(f"Dependencies: ✅ OK")
    print(f"Configuration: ✅ OK")
    print(f"Instapaper connection: {'✅ OK' if instapaper_ok else '❌ FAILED'}")
    print()

    if instapaper_ok:
        print("🎉 Configuration is valid! You can now start the webhook service.")
        print()
        print("Next steps:")
        print("1. Start the service: python app.py (or docker-compose up -d)")
        print("2. Configure Miniflux webhook to point to: http://your-server:5002/webhook")
        print("3. Test with: python test_webhook.py http://your-server:5002")
    else:
        print("⚠️  Configuration has issues. Please fix the Instapaper connection before starting the service.")
        sys.exit(1)

if __name__ == "__main__":
    main()
