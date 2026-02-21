import logging
import re
import asyncio
from datetime import datetime
from telegram import Update, ChatMember
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ChatMemberHandler
)
from telegram.constants import ParseMode
import config
from database import db

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Regular expressions for detecting links and usernames
URL_PATTERN = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*|www\.[^\s]+'
USERNAME_PATTERN = r'@(\w+)'

class ChannelBot:
    def __init__(self):
        self.application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "👋 Hello! I'm a Channel Management Bot.\n\n"
            "I automatically monitor channels I'm added to and:\n"
            "• Replace URLs with '[Link Removed]'\n"
            "• Replace usernames with default username\n"
            "• Add username to posts without links/usernames\n\n"
            "Commands:\n"
            "/set_username <username> - Set global username\n"
            "/whitelist_usernames - Manage whitelisted usernames\n"
            "/whitelist_urls - Manage whitelisted URLs\n"
            "/settings - Show current settings\n"
            "/channels - List all monitored channels\n"
            "/help - Show this help message"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)
    
    async def channels_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all channels bot is monitoring"""
        channels = await db.get_all_channels()
        
        if not channels:
            await update.message.reply_text("📝 No channels are being monitored yet.")
            return
        
        text = "📊 **Monitored Channels:**\n\n"
        for channel in channels:
            text += f"• {channel.get('channel_title', 'Unknown')} (ID: `{channel['channel_id']}`)\n"
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def set_username_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set global username"""
        if not context.args:
            await update.message.reply_text("Usage: /set_username @username")
            return
        
        username = context.args[0]
        if not username.startswith('@'):
            username = f'@{username}'
        
        await db.update_global_username(username)
        await update.message.reply_text(f"✅ Global username set to {username}")
    
    async def whitelist_usernames_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manage whitelisted usernames"""
        if len(context.args) < 1:
            whitelist = await db.get_whitelist_usernames()
            if whitelist:
                text = "📋 **Whitelisted Usernames:**\n" + "\n".join(whitelist)
            else:
                text = "📋 No usernames in whitelist."
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            return
        
        subcommand = context.args[0].lower()
        
        if subcommand == "add" and len(context.args) > 1:
            username = context.args[1]
            if not username.startswith('@'):
                username = f'@{username}'
            await db.add_to_whitelist_usernames(username)
            await update.message.reply_text(f"✅ Added {username} to whitelist")
        
        elif subcommand == "remove" and len(context.args) > 1:
            username = context.args[1]
            if not username.startswith('@'):
                username = f'@{username}'
            await db.remove_from_whitelist_usernames(username)
            await update.message.reply_text(f"✅ Removed {username} from whitelist")
        
        elif subcommand == "list":
            whitelist = await db.get_whitelist_usernames()
            if whitelist:
                text = "📋 **Whitelisted Usernames:**\n" + "\n".join(whitelist)
            else:
                text = "📋 No usernames in whitelist."
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        
        else:
            await update.message.reply_text(
                "Usage:\n"
                "/whitelist_usernames - Show all\n"
                "/whitelist_usernames add @username\n"
                "/whitelist_usernames remove @username\n"
                "/whitelist_usernames list"
            )
    
    async def whitelist_urls_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manage whitelisted URLs"""
        if len(context.args) < 1:
            whitelist = await db.get_whitelist_urls()
            if whitelist:
                text = "📋 **Whitelisted URLs:**\n" + "\n".join(whitelist)
            else:
                text = "📋 No URLs in whitelist."
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            return
        
        subcommand = context.args[0].lower()
        
        if subcommand == "add" and len(context.args) > 1:
            url = context.args[1]
            await db.add_to_whitelist_urls(url)
            await update.message.reply_text(f"✅ Added {url} to whitelist")
        
        elif subcommand == "remove" and len(context.args) > 1:
            url = context.args[1]
            await db.remove_from_whitelist_urls(url)
            await update.message.reply_text(f"✅ Removed {url} from whitelist")
        
        elif subcommand == "list":
            whitelist = await db.get_whitelist_urls()
            if whitelist:
                text = "📋 **Whitelisted URLs:**\n" + "\n".join(whitelist)
            else:
                text = "📋 No URLs in whitelist."
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        
        else:
            await update.message.reply_text(
                "Usage:\n"
                "/whitelist_urls - Show all\n"
                "/whitelist_urls add example.com\n"
                "/whitelist_urls remove example.com\n"
                "/whitelist_urls list"
            )
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show global settings"""
        settings = await db.get_global_settings()
        
        username = settings.get('username', config.DEFAULT_USERNAME)
        whitelist_usernames = settings.get('whitelist_usernames', [])
        whitelist_urls = settings.get('whitelist_urls', [])
        bot_settings = settings.get('settings', {})
        
        text = (
            f"⚙️ **Global Settings:**\n\n"
            f"**Username:** {username}\n"
            f"**Add username to all posts:** {bot_settings.get('add_username_to_all', True)}\n"
            f"**Replace links:** {bot_settings.get('replace_links', True)}\n"
            f"**Replace usernames:** {bot_settings.get('replace_usernames', True)}\n\n"
            f"**Whitelisted Usernames:** {len(whitelist_usernames)}\n"
            f"**Whitelisted URLs:** {len(whitelist_urls)}"
        )
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def track_channel_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Track when bot is added/removed from channels"""
        result = update.my_chat_member
        
        if not result:
            return
        
        chat = result.chat
        old_status = result.old_chat_member.status
        new_status = result.new_chat_member.status
        
        # Check if this is a channel
        if chat.type not in ['channel']:
            return
        
        # Bot was added to channel
        if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator']:
            # Add channel to database
            await db.add_channel(
                channel_id=chat.id,
                channel_title=chat.title or f"Channel {chat.id}",
                added_by=result.from_user.id if result.from_user else None
            )
            
            logger.info(f"Bot added to channel: {chat.title} ({chat.id})")
            
            # Try to send confirmation (may fail if bot can't message)
            try:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text="✅ Bot activated! I'll now monitor and modify posts in this channel."
                )
            except:
                pass
        
        # Bot was removed from channel
        elif new_status in ['left', 'kicked'] and old_status in ['member', 'administrator']:
            # Remove or deactivate channel
            await db.remove_channel(chat.id)
            logger.info(f"Bot removed from channel: {chat.title} ({chat.id})")
    
    async def process_channel_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process and modify channel posts"""
        if not update.channel_post:
            return
        
        channel_id = update.effective_chat.id
        
        # Check if channel is in database
        channel = await db.get_channel(channel_id)
        if not channel:
            logger.info(f"Channel {channel_id} not in database, skipping")
            return
        
        message = update.channel_post
        text = message.text or message.caption or ""
        
        if not text:
            return
        
        # Get global settings
        settings_data = await db.get_global_settings()
        default_username = settings_data.get('username', config.DEFAULT_USERNAME)
        whitelist_usernames = settings_data.get('whitelist_usernames', [])
        whitelist_urls = settings_data.get('whitelist_urls', [])
        bot_settings = settings_data.get('settings', {})
        
        modified_text = text
        modifications_made = False
        
        # Check if any modifications are needed
        needs_modification = False
        
        # Check for non-whitelisted URLs
        if bot_settings.get('replace_links', True):
            urls = re.findall(URL_PATTERN, text)
            non_whitelisted_urls = []
            
            for url in urls:
                # Check if URL contains any whitelisted domain
                is_whitelisted = False
                for whitelisted_url in whitelist_urls:
                    if whitelisted_url in url:
                        is_whitelisted = True
                        break
                
                if not is_whitelisted:
                    non_whitelisted_urls.append(url)
            
            if non_whitelisted_urls:
                needs_modification = True
        
        # Check for non-whitelisted usernames
        if bot_settings.get('replace_usernames', True):
            usernames = re.findall(USERNAME_PATTERN, text)
            non_whitelisted_usernames = []
            
            for username in usernames:
                full_username = f'@{username}'
                if full_username not in whitelist_usernames:
                    non_whitelisted_usernames.append(full_username)
            
            if non_whitelisted_usernames:
                needs_modification = True
        
        # If modifications are needed, apply them
        if needs_modification:
            modified_text = text
            
            # Replace non-whitelisted URLs
            if bot_settings.get('replace_links', True):
                def replace_url(match):
                    url = match.group(0)
                    for whitelisted in whitelist_urls:
                        if whitelisted in url:
                            return url
                    return '[Link Removed]'
                
                modified_text = re.sub(URL_PATTERN, replace_url, modified_text)
                modifications_made = True
            
            # Replace non-whitelisted usernames
            if bot_settings.get('replace_usernames', True):
                def replace_username(match):
                    username = match.group(1)
                    full_username = f'@{username}'
                    if full_username in whitelist_usernames:
                        return full_username
                    return default_username
                
                modified_text = re.sub(USERNAME_PATTERN, replace_username, modified_text)
                modifications_made = True
        
        # Add username to bottom if no modifications were made and setting enabled
        elif bot_settings.get('add_username_to_all', True):
            modified_text = f"{text}\n\n{default_username}"
            modifications_made = True
        
        # If text was modified, edit the message
        if modifications_made and modified_text != text:
            try:
                if message.text:
                    await message.edit_text(modified_text)
                elif message.caption:
                    await message.edit_caption(caption=modified_text)
                logger.info(f"Modified post in channel {channel_id}")
            except Exception as e:
                logger.error(f"Failed to edit message: {e}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
    
    async def setup(self):
        """Setup the bot"""
        # Create application
        self.application = Application.builder().token(config.BOT_TOKEN).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("channels", self.channels_command))
        self.application.add_handler(CommandHandler("set_username", self.set_username_command))
        self.application.add_handler(CommandHandler("whitelist_usernames", self.whitelist_usernames_command))
        self.application.add_handler(CommandHandler("whitelist_urls", self.whitelist_urls_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        
        # Handle chat member updates (when bot is added/removed from channels)
        self.application.add_handler(ChatMemberHandler(
            self.track_channel_member, ChatMemberHandler.MY_CHAT_MEMBER
        ))
        
        # Handle channel posts
        self.application.add_handler(MessageHandler(
            filters.ChatType.CHANNEL,
            self.process_channel_post
        ))
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
    
    async def run(self):
        """Run the bot"""
        await self.setup()
        await db.connect()
        
        try:
            logger.info("Starting bot...")
            await self.application.initialize()
            await self.application.start()
            
            # Start polling
            await self.application.updater.start_polling()
            logger.info("Bot is running. Press Ctrl+C to stop.")
            
            # Keep the bot running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
        finally:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            await db.close()

async def main():
    """Main function"""
    bot = ChannelBot()
    await bot.run()

if __name__ == '__main__':
    asyncio.run(main())
