#!/usr/bin/env python3
"""
Test script for Miniflux to Instapaper webhook service

This script sends fake webhook requests to test the service functionality.
"""

import json
import hmac
import hashlib
import requests
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_signature(payload: bytes, secret: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload"""
    if not secret:
        return ""

    signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    return signature

def create_test_payload(event_type="new_entries"):
    """Create a realistic test payload matching Miniflux webhook format"""

    if event_type == "new_entries":
        return {
            "event_type": "new_entries",
            "feed": {
                "id": 1,
                "title": "Test Feed",
                "site_url": "https://example.com",
                "feed_url": "https://example.com/feed.xml",
                "checked_at": datetime.now().isoformat() + "Z"
            },
            "entries": [
                {
                    "id": 123,
                    "title": "Top Stories: iOS 26 Public Beta Testing - MacRumors Test",
                    "url": "https://www.macrumors.com/2025/07/26/top-stories-ios-26-public-beta/",
                    "content": "This is a test article created by the webhook test script using a real MacRumors URL. It should appear in your Instapaper account if everything is working correctly.",
                    "summary": "Real MacRumors URL test article",
                    "author": "MacRumors Test",
                    "published_at": datetime.now().isoformat() + "Z",
                    "created_at": datetime.now().isoformat() + "Z",
                    "changed_at": datetime.now().isoformat() + "Z",
                    "status": "unread",
                    "reading_time": 1,
                    "enclosures": [],
                    "feed": {
                        "id": 1,
                        "title": "Test Feed"
                    }
                }
            ]
        }
    elif event_type == "save_entry":
        return {
            "event_type": "save_entry",
            "entry": {
                "id": 456,
                "title": "Saved Test Article from Webhook Test",
                "url": "https://example.com/saved-test-article",
                "content": "This is a saved test article created by the webhook test script. It should appear in your Instapaper account if everything is working correctly.",
                "summary": "Saved test article summary",
                "author": "Test Author",
                "published_at": datetime.now().isoformat() + "Z",
                "created_at": datetime.now().isoformat() + "Z",
                "changed_at": datetime.now().isoformat() + "Z",
                "status": "unread",
                "reading_time": 2,
                "enclosures": [],
                "feed": {
                    "id": 1,
                    "title": "Test Feed"
                }
            }
        }

def test_health_check(base_url):
    """Test the health check endpoint"""
    print("1. Testing health check...")
    health_url = f"{base_url}/health"
    print(f"Testing health check: {health_url}")

    try:
        response = requests.get(health_url, timeout=10)
        print(f"Health check status: {response.status_code}")
        print(f"Health check response: {response.text}")

        if response.status_code == 200:
            print("✅ Health check successful!")
            return True
        else:
            print("❌ Health check failed!")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Health check error: {e}")
        return False

def test_webhook(base_url, event_type="new_entries"):
    """Test the webhook endpoint with a fake payload"""
    print(f"\n2. Testing webhook with {event_type} event...")

    webhook_url = f"{base_url}/webhook"
    print(f"Testing webhook: {webhook_url}")
    print(f"Event type: {event_type}")

    # Create test payload
    payload = create_test_payload(event_type)
    payload_json = json.dumps(payload)
    payload_bytes = payload_json.encode('utf-8')

    # Get webhook secret from environment
    webhook_secret = os.getenv('MINIFLUX_WEBHOOK_SECRET', '')

    # Generate signature
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Miniflux/2.0.42',
        'X-Miniflux-Event-Type': event_type
    }

    if webhook_secret:
        signature = generate_signature(payload_bytes, webhook_secret)
        headers['X-Miniflux-Signature'] = signature
        print(f"Generated signature: {signature[:16]}...")
    else:
        print("⚠️  No webhook secret found - signature will not be included")

    print("Sending request...")

    try:
        response = requests.post(
            webhook_url,
            data=payload_bytes,
            headers=headers,
            timeout=10
        )

        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body: {response.text}")

        if response.status_code == 200:
            print("✅ Webhook test successful!")
            return True
        else:
            print("❌ Webhook test failed!")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Webhook test error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_webhook.py <base_url> [event_type]")
        print("Example: python test_webhook.py http://localhost:5002")
        print("Example: python test_webhook.py http://localhost:5002 save_entry")
        sys.exit(1)

    base_url = sys.argv[1].rstrip('/')
    event_type = sys.argv[2] if len(sys.argv) > 2 else "new_entries"

    if event_type not in ["new_entries", "save_entry"]:
        print("Error: event_type must be 'new_entries' or 'save_entry'")
        sys.exit(1)

    print("=== Miniflux to Instapaper Webhook Test ===")
    print()

    # Test health check
    health_ok = test_health_check(base_url)

    # Test webhook
    webhook_ok = test_webhook(base_url, event_type)

    print("\n=== Test Summary ===")
    print(f"Health check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Webhook test: {'✅ PASS' if webhook_ok else '❌ FAIL'}")

    if health_ok and webhook_ok:
        print("\nCheck your Instapaper account to see if the test article was added!")
    else:
        print("\nSome tests failed. Check the service logs for more details.")

if __name__ == "__main__":
    main()