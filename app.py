#!/usr/bin/env python3
"""
Miniflux to Instapaper Webhook Service

This service receives webhooks from Miniflux and automatically adds new articles
to Instapaper using the Simple API.
"""

import hashlib
import hmac
import json
import logging
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
MINIFLUX_WEBHOOK_SECRET = os.getenv('MINIFLUX_WEBHOOK_SECRET')
INSTAPAPER_USERNAME = os.getenv('INSTAPAPER_USERNAME')
INSTAPAPER_PASSWORD = os.getenv('INSTAPAPER_PASSWORD', '')  # Password is optional
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 5002))
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', '0.0.0.0')

# Instapaper API endpoints
INSTAPAPER_ADD_URL = 'https://www.instapaper.com/api/add'


class InstapaperClient:
    """Client for interacting with Instapaper Simple API"""

    def __init__(self, username: str, password: str = ''):
        self.username = username
        self.password = password

    def add_article(self, url: str, title: Optional[str] = None,
                   selection: Optional[str] = None) -> bool:
        """
        Add an article to Instapaper

        Args:
            url: The URL to add
            title: Optional title for the article
            selection: Optional description/selection text

        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                'username': self.username,
                'password': self.password,
                'url': url
            }

            if title:
                data['title'] = title

            if selection:
                data['selection'] = selection

            logger.info(f"Adding article to Instapaper: {title or url}")

            response = requests.post(
                INSTAPAPER_ADD_URL,
                data=data,
                timeout=30
            )

            if response.status_code == 201:
                logger.info(f"Successfully added to Instapaper: {title or url}")

                # Log additional info from headers if available
                if 'Content-Location' in response.headers:
                    logger.info(f"Saved URL: {response.headers['Content-Location']}")
                if 'X-Instapaper-Title' in response.headers:
                    logger.info(f"Detected title: {response.headers['X-Instapaper-Title']}")

                return True
            elif response.status_code == 403:
                logger.error("Invalid Instapaper credentials")
                return False
            elif response.status_code == 400:
                logger.error(f"Bad request to Instapaper API: {response.text}")
                return False
            elif response.status_code == 500:
                logger.error("Instapaper service error")
                return False
            else:
                logger.error(f"Unexpected response from Instapaper: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Instapaper: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error adding to Instapaper: {e}")
            return False


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify the webhook signature from Miniflux

    Args:
        payload: The raw request body
        signature: The X-Miniflux-Signature header value
        secret: The webhook secret from Miniflux settings

    Returns:
        True if signature is valid, False otherwise
    """
    if not secret:
        logger.warning("No webhook secret configured - skipping signature verification")
        return True

    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def process_new_entries(entries: List[Dict]) -> int:
    """
    Process a list of new entries from Miniflux

    Args:
        entries: List of entry dictionaries from webhook payload

    Returns:
        Number of entries successfully processed
    """
    if not INSTAPAPER_USERNAME:
        logger.error("Instapaper username not configured")
        return 0

    instapaper = InstapaperClient(INSTAPAPER_USERNAME, INSTAPAPER_PASSWORD)
    processed_count = 0

    for entry in entries:
        try:
            url = entry.get('url')
            title = entry.get('title', '')
            content = entry.get('content', '')

            if not url:
                logger.warning(f"Entry missing URL: {entry.get('id')}")
                continue

            # Create a description from content if available (truncated)
            description = None
            if content:
                # Strip HTML tags and truncate for description
                import re
                text_content = re.sub(r'<[^>]+>', '', content)
                if len(text_content) > 200:
                    description = text_content[:200] + '...'
                else:
                    description = text_content

            success = instapaper.add_article(
                url=url,
                title=title,
                selection=description
            )

            if success:
                processed_count += 1
                logger.info(f"Added entry {entry.get('id')} to Instapaper: {title}")
            else:
                logger.error(f"Failed to add entry {entry.get('id')} to Instapaper")

        except Exception as e:
            logger.error(f"Error processing entry {entry.get('id', 'unknown')}: {e}")

    return processed_count


def process_saved_entry(entry: Dict) -> bool:
    """
    Process a saved entry from Miniflux

    Args:
        entry: Entry dictionary from webhook payload

    Returns:
        True if successfully processed, False otherwise
    """
    if not INSTAPAPER_USERNAME:
        logger.error("Instapaper username not configured")
        return False

    instapaper = InstapaperClient(INSTAPAPER_USERNAME, INSTAPAPER_PASSWORD)

    try:
        url = entry.get('url')
        title = entry.get('title', '')
        content = entry.get('content', '')

        if not url:
            logger.warning(f"Saved entry missing URL: {entry.get('id')}")
            return False

        # Create a description from content if available (truncated)
        description = None
        if content:
            import re
            text_content = re.sub(r'<[^>]+>', '', content)
            if len(text_content) > 200:
                description = text_content[:200] + '...'
            else:
                description = text_content

        # Add a note that this was saved in Miniflux
        if description:
            description = f"[Saved from Miniflux] {description}"
        else:
            description = "[Saved from Miniflux]"

        success = instapaper.add_article(
            url=url,
            title=title,
            selection=description
        )

        if success:
            logger.info(f"Added saved entry {entry.get('id')} to Instapaper: {title}")
            return True
        else:
            logger.error(f"Failed to add saved entry {entry.get('id')} to Instapaper")
            return False

    except Exception as e:
        logger.error(f"Error processing saved entry {entry.get('id', 'unknown')}: {e}")
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})


@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """
    Handle incoming webhooks from Miniflux
    """
    try:
        # Get headers
        signature = request.headers.get('X-Miniflux-Signature', '')
        event_type = request.headers.get('X-Miniflux-Event-Type', '')

        # Get raw payload for signature verification
        payload = request.get_data()

        # Verify signature if secret is configured
        if MINIFLUX_WEBHOOK_SECRET and not verify_webhook_signature(
            payload, signature, MINIFLUX_WEBHOOK_SECRET
        ):
            logger.warning(f"Invalid webhook signature from {request.remote_addr}")
            return jsonify({'error': 'Invalid signature'}), 403

        # Parse JSON payload
        try:
            data = request.get_json()
        except Exception as e:
            logger.error(f"Invalid JSON payload: {e}")
            return jsonify({'error': 'Invalid JSON'}), 400

        if not data:
            logger.error("Empty payload received")
            return jsonify({'error': 'Empty payload'}), 400

        logger.info(f"Received webhook: {event_type} from {request.remote_addr}")

        # Process based on event type
        if event_type == 'new_entries':
            entries = data.get('entries', [])
            feed_title = data.get('feed', {}).get('title', 'Unknown feed')

            logger.info(f"Processing {len(entries)} new entries from feed: {feed_title}")

            processed_count = process_new_entries(entries)

            return jsonify({
                'status': 'success',
                'event_type': event_type,
                'entries_received': len(entries),
                'entries_processed': processed_count,
                'feed': feed_title
            })

        elif event_type == 'save_entry':
            entry = data.get('entry', {})

            logger.info(f"Processing saved entry: {entry.get('title', 'Unknown title')}")

            success = process_saved_entry(entry)

            return jsonify({
                'status': 'success' if success else 'error',
                'event_type': event_type,
                'entry_processed': success,
                'entry_title': entry.get('title', 'Unknown title')
            })

        else:
            logger.warning(f"Unknown event type: {event_type}")
            return jsonify({
                'status': 'ignored',
                'event_type': event_type,
                'message': 'Event type not supported'
            })

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with basic info"""
    return jsonify({
        'service': 'Miniflux to Instapaper Webhook',
        'version': '1.0.0',
        'endpoints': {
            'webhook': '/webhook',
            'health': '/health'
        },
        'status': 'running'
    })


if __name__ == '__main__':
    # Validate required configuration
    if not INSTAPAPER_USERNAME:
        logger.error("INSTAPAPER_USERNAME environment variable is required")
        exit(1)

    if not MINIFLUX_WEBHOOK_SECRET:
        logger.warning("MINIFLUX_WEBHOOK_SECRET not set - webhook signature verification disabled")

    logger.info(f"Starting Miniflux to Instapaper webhook service")
    logger.info(f"Instapaper username: {INSTAPAPER_USERNAME}")
    logger.info(f"Webhook signature verification: {'enabled' if MINIFLUX_WEBHOOK_SECRET else 'disabled'}")

    # Start the Flask app
    app.run(
        host=WEBHOOK_HOST,
        port=WEBHOOK_PORT,
        debug=False
    )
