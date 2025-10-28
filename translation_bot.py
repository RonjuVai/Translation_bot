import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable not set!")
    print("💡 Please set BOT_TOKEN in Railway environment variables")
    exit(1)

# Simple group settings storage
group_settings = {}

class TranslationBot:
    def __init__(self):
        self.supported_languages = {
            'bn': 'Bengali', 'hi': 'Hindi', 'ar': 'Arabic', 'es': 'Spanish',
            'fr': 'French', 'de': 'German', 'pt': 'Portuguese', 'ru': 'Russian',
            'ja': 'Japanese', 'ko': 'Korean', 'zh': 'Chinese', 'it': 'Italian',
            'ur': 'Urdu', 'ta': 'Tamil', 'te': 'Telugu', 'mr': 'Marathi'
        }
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        welcome_text = """
🌐 **Welcome to Translation Bot!**

I automatically translate non-English messages to English in groups.

**Admin Commands:**
/toggle - Enable/disable translation
/settings - Show current settings
/help - Get help guide

**Add me to your group and make me admin to start translating!**
        """
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = """
🤖 **Translation Bot Help**

**How to use:**
1. Add me to your group
2. Make me administrator
3. I'll auto-translate non-English messages

**Commands:**
/start - Start the bot
/toggle - Toggle translation (admin only)
/settings - Show settings
/help - This message

**Features:**
• 100+ languages support
• Auto language detection
• Fast translation
• Easy toggle on/off
        """
        await update.message.reply_text(help_text)

    async def toggle_translation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle translation on/off"""
        try:
            if update.message.chat.type not in ['group', 'supergroup']:
                await update.message.reply_text("❌ This command works only in groups!")
                return

            # Check admin permissions
            user = update.message.from_user
            chat_id = update.message.chat.id
            
            try:
                member = await context.bot.get_chat_member(chat_id, user.id)
                if member.status not in ['administrator', 'creator']:
                    await update.message.reply_text("❌ Only admins can use this command!")
                    return
            except Exception as e:
                logger.error(f"Permission check failed: {e}")
                await update.message.reply_text("❌ Error checking permissions!")
                return

            # Toggle setting
            current = group_settings.get(chat_id, True)
            group_settings[chat_id] = not current
            new_status = "✅ ENABLED" if group_settings[chat_id] else "❌ DISABLED"
            
            await update.message.reply_text(
                f"🔄 Translation is now **{new_status}** for this group!",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Toggle error: {e}")
            await update.message.reply_text("❌ Command failed!")

    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current settings"""
        try:
            if update.message.chat.type not in ['group', 'supergroup']:
                await update.message.reply_text("❌ This command works only in groups!")
                return

            chat_id = update.message.chat.id
            status = "✅ ENABLED" if group_settings.get(chat_id, True) else "❌ DISABLED"
            
            settings_text = f"""
⚙️ **Translation Settings**

**Status:** {status}
**Target Language:** English 🇺🇸
**Supported Languages:** 100+

Use /toggle to enable/disable translation
            """
            await update.message.reply_text(settings_text)
            
        except Exception as e:
            logger.error(f"Settings error: {e}")
            await update.message.reply_text("❌ Command failed!")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        try:
            # Skip if message from bot
            if update.message.from_user.is_bot:
                return

            # Skip if not in group or translation disabled
            if update.message.chat.type in ['group', 'supergroup']:
                chat_id = update.message.chat.id
                if not group_settings.get(chat_id, True):
                    return

            # Get message text
            text = update.message.text
            if not text or len(text.strip()) < 2:
                return

            # Skip commands
            if text.startswith('/'):
                return

            # Skip very long messages
            if len(text) > 500:
                return

            # Detect language
            try:
                detected = GoogleTranslator(source='auto').detect(text)
                if detected == 'en':
                    return  # Skip English messages
            except Exception as e:
                logger.warning(f"Language detection failed: {e}")
                detected = 'unknown'

            # Translate message
            try:
                translated = GoogleTranslator(source='auto', target='en').translate(text)
                
                if not translated or translated == text:
                    return  # Skip if translation failed or same
                    
            except Exception as e:
                logger.error(f"Translation failed: {e}")
                return

            # Prepare response
            lang_name = self.supported_languages.get(detected, detected.upper())
            response = f"**Translation** 🌐\n\n"
            response += f"**{lang_name} → English:**\n"
            response += f"`{translated}`\n\n"
            response += f"_Original:_ `{text}`"

            await update.message.reply_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Message handling error: {e}")

def main():
    """Main function to start the bot"""
    try:
        print("🚀 Starting Translation Bot...")
        
        # Check token
        if not BOT_TOKEN:
            print("❌ ERROR: BOT_TOKEN not found!")
            return

        # Create bot instance
        bot = TranslationBot()
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()

        # Add command handlers
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("help", bot.help_command))
        application.add_handler(CommandHandler("toggle", bot.toggle_translation))
        application.add_handler(CommandHandler("settings", bot.show_settings))
        
        # Add message handler (MUST be after command handlers)
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            bot.handle_message
        ))

        # Start polling
        print("✅ Bot is running successfully!")
        print("🤖 Waiting for messages...")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        print(f"❌ Fatal error: {e}")

if __name__ == '__main__':
    main()            response += f"**From {original_lang} to English:**\n"
            response += f"`{translated_text}`\n\n"
            response += f"*Original:* `{message_text[:200]}{'...' if len(message_text) > 200 else ''}`"
            
            await update.message.reply_text(
                response,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in handle_message: {e}")

    async def toggle_translation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle translation on/off for the group"""
        try:
            if update.message.chat.type not in ['group', 'supergroup']:
                await update.message.reply_text("❌ This command works only in groups!")
                return
                
            # Check if user is admin
            user_id = update.message.from_user.id
            chat_id = update.message.chat.id
            
            try:
                member = await context.bot.get_chat_member(chat_id, user_id)
                if member.status not in ['administrator', 'creator']:
                    await update.message.reply_text("❌ Only admins can use this command!")
                    return
            except Exception as e:
                logger.error(f"Admin check error: {e}")
                await update.message.reply_text("❌ Error checking permissions!")
                return
                
            # Toggle setting
            new_status = group_manager.toggle(chat_id)
            status = "✅ enabled" if new_status else "❌ disabled"
            
            await update.message.reply_text(
                f"🔄 Translation has been **{status}** for this group!",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in toggle_translation: {e}")
            await update.message.reply_text("❌ Command failed!")

    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current translation settings"""
        try:
            if update.message.chat.type not in ['group', 'supergroup']:
                await update.message.reply_text("❌ This command works only in groups!")
                return
                
            chat_id = update.message.chat.id
            is_enabled = group_manager.is_enabled(chat_id)
            
            status = "✅ Enabled" if is_enabled else "❌ Disabled"
            
            message = f"**Group Translation Settings** ⚙️\n\n"
            message += f"**Status:** {status}\n"
            message += f"**Target Language:** English 🇺🇸\n"
            message += f"**Supported Languages:** 100+\n\n"
            message += "**Admin Commands:**\n"
            message += "/toggle - Enable/disable translation\n"
            message += "/settings - Show this message\n"
            message += "/help - Get help\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_settings: {e}")
            await update.message.reply_text("❌ Command failed!")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message"""
        help_text = """
🤖 **Group Translation Bot** 🌐

I automatically translate all non-English messages in this group to English.

**Admin Commands:**
/toggle - Enable or disable translation
/settings - Show current settings
/help - Get help

**Features:**
• Auto-detects message language
• Translates to English
• Supports 100+ languages
• Easy on/off toggle

**How to use:**
1. Add me to your group
2. Make me admin to read all messages
3. I'll automatically translate messages

**Note:** I skip messages that are already in English.
        """
        
        await update.message.reply_text(help_text)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        welcome_text = """
🌐 **Welcome to Translation Bot!**

I can automatically translate messages in your groups to English.

**To use me in a group:**
1. Add me to your group
2. Make me an administrator  
3. I'll start translating automatically

**Admin Commands for Groups:**
/toggle - Turn translation on/off
/settings - Check current settings
/help - Show this help message

I support 100+ languages including:
Bengali, Hindi, Arabic, Spanish, French, German, Chinese, Japanese, and more!
        """
        
        await update.message.reply_text(welcome_text)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")

def main():
    try:
        # Create bot instance
        bot = TranslationBot()
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", bot.start_command))
        application.add_handler(CommandHandler("help", bot.help_command))
        application.add_handler(CommandHandler("toggle", bot.toggle_translation))
        application.add_handler(CommandHandler("settings", bot.show_settings))
        
        # Message handler (must be last)
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            bot.handle_message
        ))
        
        # Error handler
        application.add_error_handler(bot.error_handler)

        # Start bot
        logger.info("🌐 Translation Bot is starting...")
        print("🤖 Bot is running successfully!")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Bot crashed: {e}")

if __name__ == '__main__':
    main()            logger.error(f"Admin check error: {e}")
            await update.message.reply_text("❌ Error checking permissions!")
            return
            
        # Toggle setting
        chat_id = update.message.chat.id
        group_settings[chat_id] = not group_settings.get(chat_id, True)
        
        status = "enabled" if group_settings[chat_id] else "disabled"
        await update.message.reply_text(f"🔄 Translation has been **{status}** for this group!")

    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current translation settings"""
        if update.message.chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("This command works only in groups!")
            return
            
        chat_id = update.message.chat.id
        is_enabled = group_settings.get(chat_id, True)
        
        status = "✅ Enabled" if is_enabled else "❌ Disabled"
        
        message = f"**Group Translation Settings** ⚙️\n\n"
        message += f"**Status:** {status}\n"
        message += f"**Target Language:** English 🇺🇸\n\n"
        message += "**Commands:**\n"
        message += "/toggle - Enable/disable translation\n"
        message += "/settings - Show this message\n"
        message += "/help - Get help\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message"""
        help_text = """
🤖 **Group Translation Bot** 🌐

I automatically translate all non-English messages in this group to English.

**Admin Commands:**
/toggle - Enable or disable translation
/settings - Show current settings

**Features:**
• Auto-detects message language
• Translates to English
• Supports 100+ languages
• Easy on/off toggle

**How to use:**
1. Add me to your group
2. Make me admin to read all messages
3. I'll automatically translate messages

**Note:** I skip messages that are already in English.
        """
        
        await update.message.reply_text(help_text)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        welcome_text = """
🌐 **Welcome to Translation Bot!**

I can automatically translate messages in your groups to English.

**To use me in a group:**
1. Add me to your group
2. Make me an administrator
3. I'll start translating automatically

**Admin Commands for Groups:**
/toggle - Turn translation on/off
/settings - Check current settings
/help - Show this help message

I support 100+ languages including:
Bengali, Hindi, Arabic, Spanish, French, German, Chinese, Japanese, and more!
        """
        
        await update.message.reply_text(welcome_text)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception: {context.error}")

def main():
    # Create bot instance
    bot = TranslationBot()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        bot.handle_message
    ))
    
    # Command handlers
    from telegram.ext import CommandHandler
    
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("toggle", bot.toggle_translation))
    application.add_handler(CommandHandler("settings", bot.show_settings))
    
    # Error handler
    application.add_error_handler(bot.error_handler)

    # Start bot
    print("🌐 Translation Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
