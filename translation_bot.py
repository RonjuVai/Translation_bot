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
    print("ERROR: BOT_TOKEN environment variable not set!")
    print("Please set BOT_TOKEN in Railway environment variables")
    exit(1)

# Group settings storage
group_settings = {}

class TranslationBot:
    def __init__(self):
        self.supported_languages = {
            'bn': 'Bengali', 'hi': 'Hindi', 'ar': 'Arabic', 'es': 'Spanish',
            'fr': 'French', 'de': 'German', 'pt': 'Portuguese', 'ru': 'Russian',
            'ja': 'Japanese', 'ko': 'Korean', 'zh': 'Chinese', 'it': 'Italian',
            'ur': 'Urdu', 'ta': 'Tamil', 'te': 'Telugu', 'mr': 'Marathi'
        }
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = "🌐 Welcome to Translation Bot!\n\nI automatically translate non-English messages to English in groups.\n\nAdmin Commands:\n/toggle - Enable/disable translation\n/settings - Show current settings\n/help - Get help guide\n\nAdd me to your group and make me admin to start translating!"
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = "🤖 Translation Bot Help\n\nHow to use:\n1. Add me to your group\n2. Make me administrator\n3. I'll auto-translate non-English messages\n\nCommands:\n/start - Start the bot\n/toggle - Toggle translation (admin only)\n/settings - Show settings\n/help - This message"
        await update.message.reply_text(help_text)

    async def toggle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if update.message.chat.type not in ['group', 'supergroup']:
                await update.message.reply_text("❌ This command works only in groups!")
                return

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

            current = group_settings.get(chat_id, True)
            group_settings[chat_id] = not current
            new_status = "ENABLED" if group_settings[chat_id] else "DISABLED"
            
            await update.message.reply_text(f"🔄 Translation is now {new_status} for this group!")
            
        except Exception as e:
            logger.error(f"Toggle error: {e}")
            await update.message.reply_text("❌ Command failed!")

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if update.message.chat.type not in ['group', 'supergroup']:
                await update.message.reply_text("❌ This command works only in groups!")
                return

            chat_id = update.message.chat.id
            status = "ENABLED" if group_settings.get(chat_id, True) else "DISABLED"
            
            settings_text = f"⚙️ Translation Settings\n\nStatus: {status}\nTarget Language: English\nSupported Languages: 100+\n\nUse /toggle to enable/disable"
            await update.message.reply_text(settings_text)
            
        except Exception as e:
            logger.error(f"Settings error: {e}")
            await update.message.reply_text("❌ Command failed!")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if update.message.from_user.is_bot:
                return

            if update.message.chat.type in ['group', 'supergroup']:
                chat_id = update.message.chat.id
                if not group_settings.get(chat_id, True):
                    return

            text = update.message.text
            if not text or len(text.strip()) < 2:
                return

            if text.startswith('/'):
                return

            if len(text) > 500:
                return

            try:
                detected = GoogleTranslator(source='auto').detect(text)
                if detected == 'en':
                    return
            except Exception as e:
                logger.warning(f"Language detection failed: {e}")
                detected = 'unknown'

            try:
                translated = GoogleTranslator(source='auto', target='en').translate(text)
                
                if not translated or translated == text:
                    return
                    
            except Exception as e:
                logger.error(f"Translation failed: {e}")
                return

            lang_name = self.supported_languages.get(detected, detected.upper())
            response = f"Translation 🌐\n\n{lang_name} → English:\n{translated}\n\nOriginal: {text}"

            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Message handling error: {e}")

def main():
    try:
        print("Starting Translation Bot...")
        
        if not BOT_TOKEN:
            print("ERROR: BOT_TOKEN not found!")
            return

        bot = TranslationBot()
        
        application = Application.builder().token(BOT_TOKEN).build()

        application.add_handler(CommandHandler("start", bot.start_command))
        application.add_handler(CommandHandler("help", bot.help_command))
        application.add_handler(CommandHandler("toggle", bot.toggle_command))
        application.add_handler(CommandHandler("settings", bot.settings_command))
        
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            bot.handle_message
        ))

        print("Bot is running successfully!")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        print(f"Fatal error: {e}")

if __name__ == '__main__':
    main()