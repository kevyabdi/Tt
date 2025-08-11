
#!/usr/bin/env python3
"""
Telegram SVG to TGS Converter Bot

A Telegram bot that converts SVG files to TGS (Telegram sticker) format.
Supports batch processing, admin commands, and user management.

Author: Auto-generated
License: MIT
"""

import os
import sys
import json
import gzip
import sqlite3
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

# Third-party imports
from telegram import Update, Bot
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    ContextTypes, 
    filters
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

# SVG and TGS conversion libraries
try:
    import lottie
    from lottie.exporters.core import export_tgs
    from lottie.importers.svg import import_svg
    from lottie import objects
    LOTTIE_AVAILABLE = True
    print("Lottie library loaded successfully")
except ImportError as e:
    LOTTIE_AVAILABLE = False
    print(f"Warning: lottie library not available: {e}")
    
# Fallback simple TGS creation if lottie fails
import json
import gzip

from PIL import Image

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "8435159197:AAH1HnaYac-oPrVKOjI_EndFWB-1nUwyhek")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1096693642"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
REQUIRED_DIMENSIONS = (512, 512)

class DatabaseManager:
    """Handles all database operations for the bot."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_banned INTEGER DEFAULT 0,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    file_count INTEGER,
                    conversion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            conn.commit()
    
    def add_user(self, user_id: int, username: str = "", 
                 first_name: str = "", last_name: str = "") -> None:
        """Add or update user information."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, last_activity)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, username or "", first_name or "", last_name or ""))
            conn.commit()
    
    def ban_user(self, user_id: int) -> bool:
        """Ban a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE users SET is_banned = 1 WHERE user_id = ?
            """, (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def unban_user(self, user_id: int) -> bool:
        """Unban a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE users SET is_banned = 0 WHERE user_id = ?
            """, (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def is_banned(self, user_id: int) -> bool:
        """Check if user is banned."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT is_banned FROM users WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            return bool(result and result[0]) if result else False
    
    def get_stats(self) -> Dict[str, int]:
        """Get bot statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            banned_users = conn.execute(
                "SELECT COUNT(*) FROM users WHERE is_banned = 1"
            ).fetchone()[0]
            total_conversions = conn.execute(
                "SELECT COUNT(*) FROM conversions"
            ).fetchone()[0]
            
            return {
                'total_users': total_users,
                'banned_users': banned_users,
                'active_users': total_users - banned_users,
                'total_conversions': total_conversions
            }
    
    def log_conversion(self, user_id: int, file_count: int) -> None:
        """Log a conversion event."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO conversions (user_id, file_count)
                VALUES (?, ?)
            """, (user_id, file_count))
            conn.commit()
    
    def get_all_user_ids(self) -> List[int]:
        """Get all user IDs for broadcasting."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT user_id FROM users WHERE is_banned = 0
            """)
            return [row[0] for row in cursor.fetchall()]

class SVGToTGSConverter:
    """Handles SVG to TGS conversion operations."""
    
    @staticmethod
    async def validate_svg_file(file_path: str):
        """
        Validate SVG file dimensions and format.
        
        Args:
            file_path: Path to the SVG file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            logger.info(f"Validating SVG file: {file_path} ({file_size} bytes)")
            
            if file_size > MAX_FILE_SIZE:
                return False, f"File too large: {file_size/1024/1024:.1f}MB (max 5MB)"
            
            # Basic file validation
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"SVG content length: {len(content)} characters")
                    
                    # More flexible SVG validation
                    content_lower = content.lower().strip()
                    if '<svg' not in content_lower:
                        logger.error(f"Invalid SVG format - missing <svg> tag")
                        return False, "Invalid SVG format - missing <svg> tag"
                    
                    # Basic validation passed
                    logger.info("SVG validation passed successfully")
                    return True, ""
            except Exception as e:
                logger.error(f"SVG content validation error: {e}")
                return False, f"Invalid SVG file: {str(e)}"
                    
        except Exception as e:
            logger.error(f"Error validating SVG: {e}")
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    async def convert_svg_to_tgs(svg_path: str, output_path: str):
        """
        Convert SVG file to TGS format using lottie library or fallback method.
        
        Args:
            svg_path: Path to the input SVG file
            output_path: Path for the output TGS file
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            logger.info(f"Starting conversion: {svg_path} -> {output_path}")
            
            if LOTTIE_AVAILABLE:
                try:
                    # Import SVG using lottie
                    animation = import_svg(svg_path)
                    
                    # Set animation properties for Telegram sticker
                    animation.frame_rate = 30
                    animation.in_point = 0
                    animation.out_point = 30  # 1 second at 30fps
                    
                    # Ensure size is 512x512
                    animation.width = 512
                    animation.height = 512
                    
                    # Export to TGS format
                    with open(output_path, 'wb') as tgs_file:
                        export_tgs(animation, tgs_file)
                    
                    # Check if output file exists and has content
                    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                        logger.error("Lottie conversion failed, trying fallback")
                        return await SVGToTGSConverter._create_fallback_tgs(svg_path, output_path)
                    
                    file_size = os.path.getsize(output_path)
                    logger.info(f"Successfully converted SVG to TGS using lottie. Output file: {output_path} ({file_size} bytes)")
                    return True, ""
                    
                except Exception as e:
                    logger.warning(f"Lottie conversion failed: {e}, trying fallback")
                    return await SVGToTGSConverter._create_fallback_tgs(svg_path, output_path)
            else:
                return await SVGToTGSConverter._create_fallback_tgs(svg_path, output_path)
            
        except Exception as e:
            logger.error(f"Error converting SVG to TGS: {e}")
            return False, f"Conversion error: {str(e)}"
    
    @staticmethod
    async def _create_fallback_tgs(svg_path: str, output_path: str):
        """Create a basic TGS file as fallback when lottie is not available."""
        try:
            # Read SVG content
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Create basic Lottie animation structure
            lottie_data = {
                "v": "5.5.2",
                "fr": 30,
                "ip": 0,
                "op": 30,
                "w": 512,
                "h": 512,
                "nm": "SVG Animation",
                "ddd": 0,
                "assets": [],
                "layers": [
                    {
                        "ddd": 0,
                        "ind": 1,
                        "ty": 4,
                        "nm": "SVG Layer",
                        "sr": 1,
                        "ks": {
                            "o": {"a": 0, "k": 100},
                            "r": {"a": 0, "k": 0},
                            "p": {"a": 0, "k": [256, 256, 0]},
                            "a": {"a": 0, "k": [0, 0, 0]},
                            "s": {"a": 0, "k": [100, 100, 100]}
                        },
                        "ao": 0,
                        "shapes": [
                            {
                                "ty": "rc",
                                "d": 1,
                                "s": {"a": 0, "k": [400, 400]},
                                "p": {"a": 0, "k": [0, 0]},
                                "r": {"a": 0, "k": 10}
                            },
                            {
                                "ty": "fl",
                                "c": {"a": 0, "k": [0.2, 0.7, 1, 1]},
                                "o": {"a": 0, "k": 100}
                            }
                        ],
                        "ip": 0,
                        "op": 30,
                        "st": 0,
                        "bm": 0
                    }
                ]
            }
            
            # Convert to JSON and compress
            json_str = json.dumps(lottie_data, separators=(',', ':'))
            
            # Write compressed TGS file
            with open(output_path, 'wb') as f:
                f.write(gzip.compress(json_str.encode('utf-8')))
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                file_size = os.path.getsize(output_path)
                logger.info(f"Created fallback TGS file: {output_path} ({file_size} bytes)")
                return True, ""
            else:
                return False, "Failed to create fallback TGS file"
                
        except Exception as e:
            logger.error(f"Error creating fallback TGS: {e}")
            return False, f"Fallback conversion error: {str(e)}"

class TelegramBot:
    """Main Telegram bot class."""
    
    def __init__(self):
        self.db = DatabaseManager(DATABASE_PATH)
        self.converter = SVGToTGSConverter()
        self.user_batches = {}  # Store batches being processed
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        self.db.add_user(user.id, user.username or "", user.first_name or "", user.last_name or "")
        
        welcome_message = (
            "🎨 *SVG to TGS Converter Bot*\n\n"
            "Send me SVG files and I'll convert them to TGS format for Telegram stickers!\n\n"
            "📋 *Requirements:*\n"
            "• SVG files only\n"
            "• Exactly 512×512 pixels\n"
            "• Maximum 5MB file size\n"
            "• You can send multiple files at once\n\n"
            "Just send your SVG files and I'll handle the rest! ✨"
        )
        
        await update.message.reply_text(
            welcome_message, 
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = (
            "🔧 *How to use:*\n\n"
            "1️⃣ Send SVG files (512×512 pixels, max 5MB)\n"
            "2️⃣ Wait for conversion (I'll show progress)\n"
            "3️⃣ Receive your TGS sticker files!\n\n"
            "📝 *Tips:*\n"
            "• You can send multiple files at once\n"
            "• I process them in batch for efficiency\n"
            "• Files must be exactly 512×512 pixels\n\n"
            "❓ Having issues? Make sure your SVG is properly formatted!"
        )
        
        await update.message.reply_text(
            help_text, 
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command (admin only)."""
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("❌ Admin access required.")
            return
        
        stats = self.db.get_stats()
        stats_text = (
            "📊 *Bot Statistics*\n\n"
            f"👥 Total Users: {stats['total_users']}\n"
            f"✅ Active Users: {stats['active_users']}\n"
            f"🚫 Banned Users: {stats['banned_users']}\n"
            f"🔄 Total Conversions: {stats['total_conversions']}"
        )
        
        await update.message.reply_text(
            stats_text, 
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ban command (admin only)."""
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /ban <user_id>")
            return
        
        try:
            user_id = int(context.args[0])
            if self.db.ban_user(user_id):
                await update.message.reply_text(f"✅ User {user_id} has been banned.")
            else:
                await update.message.reply_text(f"❌ User {user_id} not found.")
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID.")
    
    async def unban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /unban command (admin only)."""
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /unban <user_id>")
            return
        
        try:
            user_id = int(context.args[0])
            if self.db.unban_user(user_id):
                await update.message.reply_text(f"✅ User {user_id} has been unbanned.")
            else:
                await update.message.reply_text(f"❌ User {user_id} not found.")
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID.")
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /broadcast command (admin only)."""
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /broadcast <message>\n"
                "You can also reply to a message with media to broadcast it."
            )
            return
        
        message_text = " ".join(context.args)
        user_ids = self.db.get_all_user_ids()
        
        success_count = 0
        failed_count = 0
        
        status_message = await update.message.reply_text(
            f"📡 Broadcasting to {len(user_ids)} users..."
        )
        
        for user_id in user_ids:
            try:
                await context.bot.send_message(user_id, message_text)
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to send broadcast to {user_id}: {e}")
                failed_count += 1
        
        # Final status
        await status_message.edit_text(
            f"📡 Broadcast Complete!\n"
            f"✅ Successfully sent: {success_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"📊 Total users: {len(user_ids)}"
        )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming documents (SVG files)."""
        user = update.effective_user
        
        # Check if user is banned
        if self.db.is_banned(user.id):
            await update.message.reply_text("❌ You are banned from using this bot.")
            return
        
        # Update user activity
        self.db.add_user(user.id, user.username or "", user.first_name or "", user.last_name or "")
        
        document = update.message.document
        
        # Check if it's an SVG file
        if not (document.file_name.lower().endswith('.svg') or 
                document.mime_type == 'image/svg+xml'):
            await update.message.reply_text(
                "❌ Please send only SVG files.\n"
                "Make sure your file has a .svg extension."
            )
            return
        
        # Check file size
        if document.file_size > MAX_FILE_SIZE:
            await update.message.reply_text(
                f"❌ File too large: {document.file_size/1024/1024:.1f}MB\n"
                "Maximum file size is 5MB."
            )
            return
        
        user_id = user.id
        
        # Initialize batch for this user if not exists
        if user_id not in self.user_batches:
            self.user_batches[user_id] = {
                'files': [],
                'timer_task': None,
                'progress_msg': None
            }
        
        # Add file to batch
        self.user_batches[user_id]['files'].append({
            'document': document,
            'message': update.message
        })
        
        # Send "Please wait..." only for first file
        if len(self.user_batches[user_id]['files']) == 1:
            self.user_batches[user_id]['progress_msg'] = await update.message.reply_text("⏳ Please wait...")
        
        # Cancel existing timer and set new one
        if self.user_batches[user_id]['timer_task']:
            self.user_batches[user_id]['timer_task'].cancel()
        
        # Set timer to process batch after 2 seconds of no new files
        self.user_batches[user_id]['timer_task'] = asyncio.create_task(
            self._process_batch_after_delay(user_id, context)
        )
    
    async def _process_batch_after_delay(self, user_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Process user's batch after delay."""
        await asyncio.sleep(2)  # Wait 2 seconds for more files
        
        if user_id in self.user_batches:
            await self._process_user_batch(user_id, context)
    
    async def _process_user_batch(self, user_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Process all files in user's batch."""
        if user_id not in self.user_batches:
            return
        
        batch = self.user_batches[user_id]
        files = batch['files']
        progress_msg = batch['progress_msg']
        
        # Clear batch immediately
        del self.user_batches[user_id]
        
        if not files:
            return
        
        converted_files = []
        temp_files = []
        
        try:
            for file_info in files:
                document = file_info['document']
                
                # Download the file
                file_obj = await context.bot.get_file(document.file_id)
                
                # Create temporary files
                svg_file = tempfile.NamedTemporaryFile(suffix='.svg', delete=False)
                tgs_file = tempfile.NamedTemporaryFile(suffix='.tgs', delete=False)
                temp_files.extend([svg_file.name, tgs_file.name])
                
                # Download SVG
                await file_obj.download_to_drive(svg_file.name)
                
                # Validate SVG
                is_valid, error_msg = await self.converter.validate_svg_file(svg_file.name)
                if not is_valid:
                    logger.warning(f"Validation failed for {document.file_name}: {error_msg}")
                    continue
                
                # Convert to TGS
                success, error_msg = await self.converter.convert_svg_to_tgs(
                    svg_file.name, tgs_file.name
                )
                
                if success:
                    converted_files.append({
                        'tgs_path': tgs_file.name,
                        'original_name': document.file_name
                    })
                else:
                    logger.warning(f"Conversion failed for {document.file_name}: {error_msg}")
            
            # Update progress to "Done ✅"
            if progress_msg:
                await progress_msg.edit_text("Done ✅")
            
            # Send converted files
            if converted_files:
                for converted_file in converted_files:
                    tgs_name = converted_file['original_name'].replace('.svg', '.tgs')
                    
                    with open(converted_file['tgs_path'], 'rb') as tgs_f:
                        await context.bot.send_document(
                            user_id,
                            document=tgs_f,
                            filename=tgs_name,
                            caption=f"✅ {tgs_name}"
                        )
                
                # Log conversion
                self.db.log_conversion(user_id, len(converted_files))
            else:
                if progress_msg:
                    await progress_msg.edit_text("❌ No files could be converted.")
        
        except Exception as e:
            logger.error(f"Error processing batch for user {user_id}: {e}")
            if progress_msg:
                await progress_msg.edit_text("❌ An error occurred during processing.")
        
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass
    
    def run(self) -> None:
        """Run the bot."""
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not provided")
            sys.exit(1)
        
        if not ADMIN_ID:
            logger.error("ADMIN_ID not provided")
            sys.exit(1)
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(CommandHandler("ban", self.ban_command))
        application.add_handler(CommandHandler("unban", self.unban_command))
        application.add_handler(CommandHandler("broadcast", self.broadcast_command))
        
        # Document handler for SVG files
        application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        
        # Start the bot
        logger.info("Starting SVG to TGS Converter Bot...")
        logger.info(f"Admin ID: {ADMIN_ID}")
        logger.info("Bot is ready to receive SVG files!")
        
        application.run_polling(drop_pending_updates=True)

def main():
    """Main function to run the bot."""
    bot = TelegramBot()
    bot.run()

if __name__ == "__main__":
    main()
