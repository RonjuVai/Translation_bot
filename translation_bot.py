import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator
from typing import Dict

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not set!")

# Store group settings with persistence
class GroupManager:
    def __init__(self):
        self.group_settings: Dict[int, bool] = {}
        self.supported_languages = {
            'bn': 'Bengali', 'hi': 'Hindi', 'ar': 'Arabic', 'es': 'Spanish', 
            'fr': 'French', 'de': 'German', 'pt': 'Portuguese', 'ru': 'Russian',
            'ja': 'Japanese', 'ko': 'Korean', 'zh': 'Chinese', 'it': 'Italian',
            'ur': 'Urdu', 'ta': 'Tamil', 'te': 'Telugu', 'mr': 'Marathi',
            'gu': 'Gujarati', 'pa': 'Punjabi', 'ml': 'Malayalam', 'kn': 'Kannada'
        }
    
    def is_enabled(self, chat_id: int) -> bool:
        return self.group_settings.get(chat_id, True)
    
    def toggle(self, chat_id: int) -> bool:
        self.group_settings[chat_id] = not self.group_settings.get(chat_id, True)
        return self.group_settings[chat_id]

group_manager = GroupManager()

class TranslationBot:
    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='en')
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Ignore if message is from bot itself
            if update.message.from_user.is_bot:
                return
                
            # Check if message is from a group
            if update.message.chat.type in ['group', 'supergroup']:
                chat_id = update.message.chat.id
                
                # Check if translation is enabled for this group
                if not group_manager.is_enabled(chat_id):
                    return
                    
            # Get message text
            message_text = update.message.text or update.message.caption
            
            # Skip if message is empty or too short
            if not message_text or len(message_text.strip()) < 2:
                return
                
            # Skip if message is a command
            if message_text.startswith('/'):
                return
                
            # Skip very long messages
            if len(message_text) > 1000:
                await update.message.reply_text("❌ Message too long for translation!")
                return

            # Detect language first
            try:
                detected_lang = GoogleTranslator(source='auto').detect(message_text)
                logger.info(f"Detected language: {detected_lang}")
                
                # If message is already in English, skip translation
                if detected_lang == 'en':
                    return
                    
            except Exception as e:
                logger.warning(f"Language detection failed: {e}")
                detected_lang = 'unknown'

            # Translate message to English
            try:
                translated_text = GoogleTranslator(source='auto', target='en').translate(message_text)
                
                if not translated_text or translated_text == message_text:
                    return
                    
            except Exception as e:
                logger.error(f"Translation failed: {e}")
                await update.message.reply_text("❌ Translation failed. Please try again.")
                return

            # Add original language info
            original_lang = group_manager.supported_languages.get(detected_lang, detected_lang.upper())
            
            # Prepare response
            response = f"**Translation** 🌐\n\n"
            response += f"**From {original_lang} to English:**\n"
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
