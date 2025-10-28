import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator
from typing import Dict, Set

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Store group settings
group_settings: Dict[int, bool] = {}
user_languages: Dict[int, str] = {}

class TranslationBot:
    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='en')
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Ignore if message is from bot itself
        if update.message.from_user.id == context.bot.id:
            return
            
        # Check if message is from a group
        if update.message.chat.type in ['group', 'supergroup']:
            chat_id = update.message.chat.id
            
            # Initialize group settings if not exists
            if chat_id not in group_settings:
                group_settings[chat_id] = True  # Default enabled
                
            # Check if translation is enabled for this group
            if not group_settings[chat_id]:
                return
                
            # Get message text
            message_text = update.message.text
            
            # Skip if message is empty or too short
            if not message_text or len(message_text.strip()) < 2:
                return
                
            # Skip if message is a command
            if message_text.startswith('/'):
                return
                
            try:
                # Detect language first
                detected_lang = GoogleTranslator(source='auto').detect(message_text)
                
                # If message is already in English, skip translation
                if detected_lang == 'en':
                    return
                    
                # Translate message to English
                translated_text = self.translator.translate(message_text)
                
                # Add original language info
                language_names = {
                    'bn': 'Bengali', 'hi': 'Hindi', 'ar': 'Arabic', 
                    'es': 'Spanish', 'fr': 'French', 'de': 'German',
                    'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
                    'ko': 'Korean', 'zh': 'Chinese', 'it': 'Italian'
                }
                
                original_lang = language_names.get(detected_lang, detected_lang)
                
                # Send translation as reply
                response = f"**Translation** 🌐\n\n"
                response += f"**From {original_lang} to English:**\n"
                response += f"`{translated_text}`\n\n"
                response += f"*Original: {message_text}*"
                
                await update.message.reply_text(
                    response,
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Translation error: {e}")
                # Don't send error message to avoid spam
                
    async def toggle_translation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle translation on/off for the group"""
        if update.message.chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("This command works only in groups!")
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