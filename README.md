# Miniflux to Instapaper Webhook Service

A Python microservice that automatically forwards new articles from Miniflux RSS feeds to your Instapaper account using webhooks.

## Features

- **Webhook Listener**: Receives webhooks from Miniflux when new articles are discovered
- **Automatic Forwarding**: Sends articles to Instapaper using the Simple API
- **Signature Verification**: Validates webhook authenticity using HMAC-SHA256
- **Docker Support**: Ready-to-deploy Docker container
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Health Checks**: Built-in health check endpoint for monitoring
- **Error Handling**: Graceful handling of API errors and network issues

## Quick Start

### Prerequisites

1. **Instapaper Account**: You need an Instapaper account
2. **Miniflux Instance**: You need a running Miniflux instance with admin access
3. **Server/Hosting**: A server or hosting platform to run the webhook service

### 1. Docker Compose

```yaml
services:
  miniflux-to-instapaper:
    image: ghcr.io/dylanfrankcom/miniflux-to-instapaper:latest
    ports:
      - "5002:5002"
    environment:
      - MINIFLUX_WEBHOOK_SECRET=${MINIFLUX_WEBHOOK_SECRET}
      - INSTAPAPER_USERNAME=${INSTAPAPER_USERNAME}
      - INSTAPAPER_PASSWORD=${INSTAPAPER_PASSWORD}
      - WEBHOOK_HOST=0.0.0.0
      - WEBHOOK_PORT=5002
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 2. Configure Environment Variables

Edit the `.env` file with your credentials:

```bash
# Get this from Miniflux Settings > Integrations > Webhook
MINIFLUX_WEBHOOK_SECRET=your_webhook_secret_from_miniflux_settings

# Your Instapaper credentials
INSTAPAPER_USERNAME=your_instapaper_username_or_email
INSTAPAPER_PASSWORD=your_instapaper_password_if_you_have_one

# Server configuration (optional)
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=5002
```

| Variable | Required | Description |
|----------|----------|-------------|
| `MINIFLUX_WEBHOOK_SECRET` | **Required** | Webhook secret from Miniflux for signature verification |
| `INSTAPAPER_USERNAME` | **Required** | Your Instapaper username or email address |
| `INSTAPAPER_PASSWORD` | Optional | Your Instapaper password (if set) |
| `WEBHOOK_HOST` | Optional | Host to bind the webhook server (default: 0.0.0.0) |
| `WEBHOOK_PORT` | Optional | Port for the webhook server (default: 5002) |

### 3. Configure Miniflux Webhook

1. Go to Miniflux Settings → Integrations → Webhook
2. Set the webhook URL to: `http://your-server:5002/webhook`
3. Copy the auto-generated secret to your `.env` file as `MINIFLUX_WEBHOOK_SECRET`
4. Save the webhook configuration

### 4. Run with Docker Compose

```bash
docker-compose up -d
```

## Webhook Events

The service handles two types of Miniflux webhook events:

### 1. New Entries (`new_entries`)

- Triggered when Miniflux discovers new articles in RSS feeds
- Automatically adds all new articles to Instapaper
- Includes article title, URL, and description (from content)

### 2. Saved Entries (`save_entry`)

- Triggered when you manually save an article in Miniflux
- Adds the saved article to Instapaper
- Useful for articles you want to read later

> [!NOTE]
> To avoid duplicate articles, disable Miniflux's built-in Instapaper integration in Settings → Integrations → Instapaper.

## Troubleshooting

### Common Issues

1. **403 Forbidden from Instapaper**
   - Check your Instapaper username and password
   - Verify credentials by logging into Instapaper directly

2. **Invalid Webhook Signature**
   - Ensure `MINIFLUX_WEBHOOK_SECRET` matches the secret in Miniflux settings
   - Check that the webhook URL in Miniflux is correct

3. **Connection Errors**
   - Verify network connectivity to instapaper.com
   - Check firewall settings

4. **Articles Not Appearing in Instapaper**
   - Check logs for error messages
   - Verify the webhook is being triggered in Miniflux
   - Test the health endpoint to ensure the service is running

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:

1. Check the logs for error messages
2. Review the troubleshooting section
3. Open an issue on GitHub with relevant log output
