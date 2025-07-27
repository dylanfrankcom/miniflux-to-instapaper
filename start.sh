#!/bin/bash

# Miniflux to Instapaper Webhook Service Startup Script

echo "=== Miniflux to Instapaper Webhook Service ==="
echo

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.sample to .env and configure your credentials:"
    echo "  cp .env.sample .env"
    echo "  # Edit .env with your Miniflux and Instapaper credentials"
    exit 1
fi

# Source environment variables
source .env

# Check required environment variables
if [ -z "$INSTAPAPER_USERNAME" ]; then
    echo "❌ INSTAPAPER_USERNAME not set in .env file"
    exit 1
fi

echo "✅ Configuration loaded"
echo "📧 Instapaper username: $INSTAPAPER_USERNAME"
echo "🔐 Webhook secret: ${MINIFLUX_WEBHOOK_SECRET:+configured}"
echo "🌐 Server: ${WEBHOOK_HOST:-0.0.0.0}:${WEBHOOK_PORT:-5002}"
echo

# Start the service
echo "🚀 Starting webhook service..."
python app.py
