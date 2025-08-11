# Deployment Guide

This document provides comprehensive deployment instructions for the SVG to TGS Converter Bot.

## Quick Deploy to Render (Recommended)

### Prerequisites
- GitHub account
- Render account (free tier available)
- Telegram Bot Token from @BotFather
- Your Telegram User ID from @userinfobot

### Steps

1. **Fork this repository** to your GitHub account

2. **Create Render Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" and select "Web Service"
   - Connect your forked repository
   - Configure the service:

   **Basic Settings:**
   ```
   Name: svg-to-tgs-bot
   Environment: Python 3
   Build Command: pip install python-telegram-bot==20.8 lottie[all] pillow cairosvg python-dotenv
   Start Command: python main.py
   ```

3. **Set Environment Variables**
   In Render dashboard, add these environment variables:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_ID=your_telegram_user_id_number
   ENVIRONMENT=production
   DATABASE_PATH=bot_database.db
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Your bot will be live!

## Deploy with Docker

### Using Docker Compose (Recommended)

1. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   services:
     svg-tgs-bot:
       build: .
       environment:
         - BOT_TOKEN=${BOT_TOKEN}
         - ADMIN_ID=${ADMIN_ID}
         - DATABASE_PATH=/app/data/bot_database.db
       volumes:
         - bot_data:/app/data
       restart: unless-stopped

   volumes:
     bot_data:
   ```

2. **Create .env file**
   ```env
   BOT_TOKEN=your_bot_token_here
   ADMIN_ID=your_user_id
   ```

3. **Deploy**
   ```bash
   docker-compose up -d
   ```

### Using Docker directly

```bash
# Build the image
docker build -t svg-tgs-bot .

# Run the container
docker run -d \
  --name svg-tgs-bot \
  -e BOT_TOKEN="your_bot_token" \
  -e ADMIN_ID="your_user_id" \
  -v bot_data:/app/data \
  --restart unless-stopped \
  svg-tgs-bot
```

## Deploy to Railway

1. **Connect Repository**
   - Go to [Railway](https://railway.app)
   - Create new project from GitHub repo

2. **Configure Environment**
   ```
   BOT_TOKEN=your_bot_token
   ADMIN_ID=your_user_id
   PYTHONUNBUFFERED=1
   ```

3. **Deploy**
   - Railway auto-deploys from main branch
   - Monitor logs for startup confirmation

## Deploy to Heroku

1. **Create Heroku App**
   ```bash
   heroku create your-bot-name
   ```

2. **Set Environment Variables**
   ```bash
   heroku config:set BOT_TOKEN="your_bot_token"
   heroku config:set ADMIN_ID="your_user_id"
   ```

3. **Create Procfile**
   ```
   worker: python main.py
   ```

4. **Deploy**
   ```bash
   git push heroku main
   heroku ps:scale worker=1
   ```

## Local Development

1. **Setup Environment**
   ```bash
   git clone https://github.com/username/svg-to-tgs-bot.git
   cd svg-to-tgs-bot
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Install Dependencies**
   ```bash
   pip install python-telegram-bot==20.8 lottie[all] pillow cairosvg python-dotenv
   ```

3. **Run Bot**
   ```bash
   python main.py
   ```

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `BOT_TOKEN` | ✅ | Telegram bot token from @BotFather | `1234567890:ABC...` |
| `ADMIN_ID` | ✅ | Your Telegram user ID | `123456789` |
| `DATABASE_PATH` | ❌ | SQLite database file path | `bot_database.db` |
| `ENVIRONMENT` | ❌ | Deployment environment | `production` |

## System Requirements

### Production
- **Memory**: 512MB minimum, 1GB recommended
- **Storage**: 1GB for database and temporary files
- **CPU**: 1 core sufficient for moderate usage
- **OS**: Linux (Ubuntu/Debian recommended)

### Dependencies
- **Python**: 3.8 or higher
- **System Libraries**: libcairo2-dev, libpango1.0-dev (for full SVG support)

## Monitoring and Logs

### Check Bot Status
```bash
# Docker
docker logs svg-tgs-bot

# Heroku
heroku logs --tail

# Railway/Render
Check dashboard logs
```

### Key Log Messages
```
Starting SVG to TGS Converter Bot...
Admin ID: 123456789
Bot is ready to receive SVG files!
```

## Troubleshooting

### Common Issues

**Bot not responding:**
- Verify BOT_TOKEN is correct
- Check bot is not blocked by Telegram
- Ensure webhook conflicts are resolved

**Import errors:**
- Verify all dependencies are installed
- Check Python version compatibility
- Install system libraries if needed

**Database errors:**
- Ensure write permissions for database file
- Check disk space availability
- Verify DATABASE_PATH is correct

### Health Check
Create a simple health check endpoint:
```bash
curl -f http://localhost:8000/health || exit 1
```

## Scaling

### High Usage Optimization
- Use connection pooling for database
- Implement file processing queue
- Add monitoring and alerting
- Consider horizontal scaling

### Performance Tips
- Monitor memory usage during peak times
- Optimize temporary file cleanup
- Use async operations for file processing
- Implement rate limiting if needed

## Security

### Production Checklist
- ✅ Environment variables secured
- ✅ Database access restricted
- ✅ File upload validation enabled
- ✅ Admin commands protected
- ✅ Error messages don't expose secrets
- ✅ Temporary files auto-cleanup

### Best Practices
- Regularly update dependencies
- Monitor for security vulnerabilities
- Use HTTPS for all communications
- Implement proper logging without sensitive data
- Regular backups of user data

## Support

For deployment issues:
1. Check the troubleshooting section above
2. Review logs for error messages
3. Verify environment variables
4. Test with a simple SVG file
5. Create an issue on GitHub if problems persist

Remember: The bot needs proper environment variables to start. Double-check your BOT_TOKEN and ADMIN_ID before deployment.