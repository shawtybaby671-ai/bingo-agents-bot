import os
from telegram import Bot
from telegram.ext import Updater, CommandHandler

# Environment variables for secrets
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID', '-1001234567890'))

# Initialize bot
bot = Bot(token=TELEGRAM_TOKEN)

def start(update, context):
    update.message.reply_text("Bot is running!")

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))

    # Start polling
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()