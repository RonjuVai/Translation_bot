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

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN not set!")
    exit(1)

group_settings = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 Translation Bot - Use /toggle to enable/disable translation")

async def toggle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("❌ Groups only!")
            return

        chat_id = update.message.chat.id
        current = group_settings.get(chat_id, True)
        group_settings[chat_id] = not current
        status = "ENABLED" if group_settings[chat_id] else "DISABLED"
        await update.message.reply_text(f"🔄 Translation {status}!")
        
    except Exception as e:
        await update.message.reply_text("❌ Command failed!")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    status = "ENABLED" if group_settings.get(chat_id, True) else "DISABLED"
    await update.message.reply_text(f"⚙️ Status: {status}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.from_user.is_bot:
            return

        if update.message.chat.type in ['group', 'supergroup']:
            chat_id = update.message.chat.id
            if not group_settings.get(chat_id, True):
                return

        text = update.message.text
        if not text or len(text.strip()) < 2 or text.startswith('/') or len(text) > 500:
            return

        detected = GoogleTranslator(source='auto').detect(text)
        if detected == 'en':
            return

        translated = GoogleTranslator(source='auto', target='en').translate(text)
        if not translated or translated == text:
            return

        await update.message.reply_text(f"🌐 Translation:\n{translated}")
    except Exception:
        pass

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("toggle", toggle_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot running...")
    application.run_polling()

if __name__ == '__main__':
    main()
