# SVG to TGS Converter Bot 🎨

A Telegram bot that converts SVG files to TGS (Telegram Animated Stickers) format with batch processing support.

## Features ✨

- **SVG to TGS Conversion**: Convert SVG files to Telegram sticker format
- **Batch Processing**: Send multiple files, get single "Please wait..." message
- **Admin Controls**: User management, statistics, broadcasting
- **File Validation**: Ensures proper SVG format and dimensions
- **Database Storage**: SQLite for user management and conversion tracking

## Requirements 📋

### SVG File Requirements
- **Format**: SVG files only (.svg extension)
- **Dimensions**: Exactly 512×512 pixels
- **File Size**: Maximum 5MB per file
- **Content**: Valid SVG markup that can be rendered

### Technical Requirements
- Python 3.8 or higher
- Telegram Bot Token (from @BotFather)
- Admin User ID (from @userinfobot)
- SQLite database (automatically created)

## Quick Start 🚀

### 1. Get Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot with `/newbot`
3. Follow the prompts and copy your bot token

### 2. Get Your Admin ID
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your numerical user ID

### 3. Local Development

Clone the repository:
```bash
git clone <your-repo-url>
cd svg-to-tgs-bot
```

Create environment file:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_user_id
DATABASE_PATH=bot_database.db
ENVIRONMENT=development
```

Install dependencies and run:
```bash
pip install python-telegram-bot lottie[all] pillow cairosvg python-dotenv
python main.py
```

### 4. Deploy to Render 🌐

1. **Fork this repository** to your GitHub account

2. **Create a new Web Service** on [Render](https://render.com)
   - Connect your GitHub repository
   - Choose "Python" environment
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`

3. **Set Environment Variables** in Render dashboard:
   ```
   BOT_TOKEN=your_bot_token_here
   ADMIN_ID=your_telegram_user_id
   ENVIRONMENT=production
   DATABASE_PATH=bot_database.db
   ```

4. **Deploy** - Your bot will be live in minutes!

## How It Works 🔄

### Single File Conversion
1. User sends an SVG file to the bot
2. Bot shows "Please wait..." for 2 seconds
3. Bot validates file (512×512 pixels, max 5MB)
4. Bot converts SVG to TGS format using Lottie library
5. Bot updates message to "Done ✅" and sends the TGS file

### Multiple Files (Batch Processing)
1. User sends multiple SVG files at once (e.g., 10 files)
2. Bot shows "Please wait..." once
3. Bot processes all files together in sequence
4. Bot sends converted TGS files one by one
5. No repeated "Please wait..." messages

## Bot Commands 🤖

### User Commands
- `/start` - Welcome message and instructions
- `/help` - Usage instructions and tips

### Admin Commands (Admin only)
- `/stats` - Bot usage statistics
- `/ban <user_id>` - Ban a user
- `/unban <user_id>` - Unban a user
- `/broadcast <message>` - Send message to all users

## File Structure 📁

```
svg-to-tgs-bot/
├── main.py              # Main bot application
├── requirements.txt     # Python dependencies
├── render.yaml         # Render deployment config
├── README.md           # This file
├── DEPLOYMENT.md       # Detailed deployment guide
├── LICENSE             # MIT license
└── bot_database.db     # SQLite database (auto-created)
```

## Environment Variables 🔧

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `BOT_TOKEN` | ✅ | Telegram bot token from @BotFather | `1234567890:ABC...` |
| `ADMIN_ID` | ✅ | Your Telegram user ID | `123456789` |
| `DATABASE_PATH` | ❌ | SQLite database file path | `bot_database.db` |
| `ENVIRONMENT` | ❌ | Deployment environment | `production` |

## Troubleshooting 🔧

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

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support 💬

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for errors
3. Create an issue on GitHub
4. Provide sample SVG files if relevant

---

**Note**: The bot creates valid TGS files suitable for Telegram stickers. Each conversion produces 3-5KB files with proper gzip headers.