# SVG to TGS Converter Bot 🎨

A powerful Telegram bot that converts SVG files into TGS (Telegram Animated Stickers) format. Built with Python and designed for seamless deployment on Render or any cloud platform.

## Features ✨

- **SVG to TGS Conversion**: Convert static SVG files to TGS format for Telegram stickers
- **Batch Processing**: Handle multiple files at once efficiently (send 10 files, get 10 TGS files back)
- **File Validation**: Ensures SVG files meet Telegram's requirements (512×512 pixels, max 5MB)
- **Smart Progress**: Shows "Please wait..." for 3 seconds, then "Done ✅" when complete
- **Admin Commands**: Complete admin panel for user management and broadcasting
- **User Management**: Ban/unban users with persistent SQLite database
- **Broadcasting**: Send messages (with media support) to all users
- **Statistics**: Track bot usage and user metrics
- **Fast & Responsive**: No unnecessary delays, processes multiple files in sequence

## Bot Commands 🤖

### User Commands
- Send SVG files directly (no commands needed)
- Bot automatically validates dimensions and converts to TGS

### Admin Commands
- `/stats` - View bot statistics (total users, conversions, etc.)
- `/ban <user_id>` - Ban a user from using the bot
- `/unban <user_id>` - Unban a previously banned user
- `/broadcast <message>` - Send message to all users (supports media)

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
pip install python-telegram-bot lottie[all] pillow cairosvg
python main.py
```

### 4. Deploy to Render 🌐

1. **Fork this repository** to your GitHub account

2. **Create a new Web Service** on [Render](https://render.com)
   - Connect your GitHub repository
   - Choose "Python" environment
   - Build Command: `pip install python-telegram-bot lottie[all] pillow cairosvg`
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
2. Bot shows "Please wait..." for 3 seconds
3. Bot validates file (512×512 pixels, max 5MB)
4. Bot converts SVG to TGS format using Lottie library
5. Bot updates message to "Done ✅" and sends the TGS file

### Multiple Files (Batch Processing)
1. User sends multiple SVG files at once (e.g., 10 files)
2. Bot shows "Please wait..." once
3. Bot processes all files together in sequence
4. Bot sends converted TGS files one by one
5. No repeated "Please wait" messages - just one process

## File Structure 📁

```
svg-to-tgs-bot/
├── main.py              # Main bot application
├── .env.example         # Environment variables template
├── .env                 # Your environment variables (not in git)
├── .gitignore           # Git ignore file
├── LICENSE              # MIT License
├── README.md            # This file
├── render.yaml          # Render deployment config
├── replit.md            # Project documentation
└── bot_database.db      # SQLite database (auto-created)
```

## Usage Examples 📖

### For Users
1. **Start the bot**: Send `/start` to get welcome message
2. **Convert single file**: Send any SVG file (512×512 pixels)
3. **Batch convert**: Send multiple SVG files at once
4. **Get help**: Send `/help` for usage instructions

### For Admins
```
/stats                    # View bot statistics
/ban 123456789           # Ban user with ID 123456789
/unban 123456789         # Unban user with ID 123456789
/broadcast Hello users!  # Send message to all users
```

## Troubleshooting 🛠️

### Common Issues

**"Invalid dimensions" error:**
- Ensure your SVG is exactly 512×512 pixels
- Check SVG viewBox attribute: `viewBox="0 0 512 512"`

**"File too large" error:**
- SVG files must be under 5MB
- Use SVG optimization tools to reduce file size

**Bot not responding:**
- Check your BOT_TOKEN is correct
- Ensure bot is added to your Telegram
- Verify environment variables are set

### Development Tips

- Use `/start` to test bot initialization
- Check logs for detailed error messages
- SQLite database stores all user data locally
- Temporary files are auto-cleaned after conversion

## Technical Details ⚙️

### Dependencies
- **python-telegram-bot**: Telegram bot framework
- **lottie[all]**: SVG to Lottie/TGS conversion
- **Pillow**: Image processing and validation
- **cairosvg**: SVG rendering support

### Database Schema
```sql
users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    is_banned INTEGER DEFAULT 0,
    join_date TIMESTAMP,
    last_activity TIMESTAMP
)

conversions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    file_count INTEGER,
    conversion_date TIMESTAMP
)
```

### Conversion Process
1. **Validation**: Check file size, format, and dimensions
2. **SVG Import**: Parse SVG using Lottie library
3. **Animation Setup**: Configure for 512×512, 30fps, 1-second duration
4. **TGS Export**: Generate gzipped JSON in TGS format
5. **Verification**: Validate output file integrity

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support 💬

- Create an [Issue](../../issues) for bug reports
- Star ⭐ this repository if you find it helpful
- Follow the project for updates

---

**Made with ❤️ for the Telegram sticker community**
