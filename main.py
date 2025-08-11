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
import lottie
from PIL import Image
# Note: cairosvg requires system cairo library which may not be available
# For deployment, ensure cairo is installed or use a simpler conversion method
CAIRO_AVAILABLE = False
try:
    import cairosvg
    CAIRO_AVAILABLE = True
except (ImportError, OSError) as e:
    print(f"cairosvg not available - SVG rendering will be limited: {e}")
    # This is normal in environments without system cairo libraries

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
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
    async def validate_svg_file(file_path: str) -> tuple[bool, str]:
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
                        logger.error(f"Invalid SVG format - missing <svg> tag in content: {content[:200]}")
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
    async def convert_svg_to_tgs(svg_path: str, output_path: str) -> tuple[bool, str]:
        """
        Convert SVG file to TGS format using lottie_convert.py command line tool.
        
        Args:
            svg_path: Path to the input SVG file
            output_path: Path for the output TGS file
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            logger.info(f"Starting conversion: {svg_path} -> {output_path}")
            
            # Use the lottie_convert.py script directly
            lottie_convert_path = "/home/runner/workspace/.pythonlibs/bin/lottie_convert.py"
            cmd = [
                'python', lottie_convert_path,
                svg_path,
                output_path,
                '--sanitize',  # Apply Telegram sticker requirements
                '--width', '512',   # Force width to 512
                '--height', '512',  # Force height to 512
                '--fps', '30'       # Set frame rate
            ]
            
            logger.info(f"Running conversion command: {' '.join(cmd)}")
            
            # Run conversion in subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Log output for debugging
            if stdout:
                logger.info(f"Conversion stdout: {stdout.decode('utf-8')}")
            if stderr:
                logger.warning(f"Conversion stderr: {stderr.decode('utf-8')}")
            
            # Check if conversion was successful
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                logger.error(f"Conversion failed with return code {process.returncode}: {error_msg}")
                return False, f"Conversion failed: {error_msg}"
            
            # Check if output file exists and has content
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                logger.error("Conversion completed but no TGS file was generated")
                return False, "No TGS file was generated"
            
            # Validate TGS file size (should be under 64KB for Telegram)
            file_size = os.path.getsize(output_path)
            if file_size > 64 * 1024:  # 64KB limit
                logger.warning(f"Generated TGS file is {file_size} bytes, which exceeds Telegram's 64KB limit")
            
            logger.info(f"Successfully converted SVG to TGS. Output file: {output_path} ({file_size} bytes)")
            return True, ""
            
        except Exception as e:
            logger.error(f"Error converting SVG to TGS: {e}")
            return False, f"Conversion error: {str(e)}"

class TelegramBot:
    """Main Telegram bot class."""
    
    def __init__(self):
        self.db = DatabaseManager(DATABASE_PATH)
        self.converter = SVGToTGSConverter()
        self.pending_files = {}  # Store files being processed by user
    
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
        
        # Check if replying to a message with media
        if update.message.reply_to_message:
            reply_msg = update.message.reply_to_message
            
            for user_id in user_ids:
                try:
                    if reply_msg.photo:
                        await context.bot.send_photo(
                            user_id, 
                            reply_msg.photo[-1].file_id, 
                            caption=message_text
                        )
                    elif reply_msg.video:
                        await context.bot.send_video(
                            user_id, 
                            reply_msg.video.file_id, 
                            caption=message_text
                        )
                    elif reply_msg.document:
                        await context.bot.send_document(
                            user_id, 
                            reply_msg.document.file_id, 
                            caption=message_text
                        )
                    else:
                        await context.bot.send_message(user_id, message_text)
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to send broadcast to {user_id}: {e}")
                    failed_count += 1
                
                # Update status every 10 messages
                if (success_count + failed_count) % 10 == 0:
                    await status_message.edit_text(
                        f"📡 Progress: {success_count + failed_count}/{len(user_ids)}\n"
                        f"✅ Sent: {success_count} | ❌ Failed: {failed_count}"
                    )
        else:
            # Text-only broadcast
            for user_id in user_ids:
                try:
                    await context.bot.send_message(user_id, message_text)
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send broadcast to {user_id}: {e}")
                    failed_count += 1
                
                # Update status every 10 messages
                if (success_count + failed_count) % 10 == 0:
                    await status_message.edit_text(
                        f"📡 Progress: {success_count + failed_count}/{len(user_ids)}\n"
                        f"✅ Sent: {success_count} | ❌ Failed: {failed_count}"
                    )
        
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
        
        # Store file for batch processing
        user_id = user.id
        if user_id not in self.pending_files:
            self.pending_files[user_id] = {
                'files': [],
                'progress_msg': None,
                'processing': False
            }
        
        self.pending_files[user_id]['files'].append({
            'document': document,
            'message': update.message
        })
        
        # Send "Please wait..." only for the first file
        if len(self.pending_files[user_id]['files']) == 1 and not self.pending_files[user_id]['processing']:
            self.pending_files[user_id]['progress_msg'] = await update.message.reply_text("⏳ Please wait...")
            self.pending_files[user_id]['processing'] = True
            
            # Wait for potential additional files
            await asyncio.sleep(3)
            
            # Process all collected files
            if user_id in self.pending_files and self.pending_files[user_id]['files']:
                await self.process_user_files(user_id, context)
    
    async def process_user_files(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process all pending files for a user."""
        if user_id not in self.pending_files or not self.pending_files[user_id]['files']:
            return
        
        user_data = self.pending_files[user_id]
        files_to_process = user_data['files'].copy()
        progress_msg = user_data['progress_msg']
        
        # Clear pending files immediately to prevent double processing
        del self.pending_files[user_id]
        
        converted_files = []
        temp_files = []
        
        try:
            for i, file_info in enumerate(files_to_process):
                document = file_info['document']
                
                # Update progress (only if multiple files)
                if len(files_to_process) > 1:
                    await progress_msg.edit_text(
                        f"🔄 Processing {i+1}/{len(files_to_process)}: {document.file_name}"
                    )
                
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
                    await progress_msg.edit_text(f"❌ Error with {document.file_name}: {error_msg}")
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
                    await progress_msg.edit_text(f"❌ Conversion failed for {document.file_name}: {error_msg}")
            
            # Send converted files
            if converted_files:
                await progress_msg.edit_text("Done ✅")
                
                for converted_file in converted_files:
                    tgs_name = converted_file['original_name'].replace('.svg', '.tgs')
                    
                    with open(converted_file['tgs_path'], 'rb') as tgs_f:
                        await context.bot.send_document(
                            user_id,
                            document=tgs_f,
                            filename=tgs_name,
                            caption=f"✅ Converted: {tgs_name}"
                        )
                
                # Log conversion
                self.db.log_conversion(user_id, len(converted_files))
            
            else:
                await progress_msg.edit_text("❌ No files could be converted.")
        
        except Exception as e:
            logger.error(f"Error processing files for user {user_id}: {e}")
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