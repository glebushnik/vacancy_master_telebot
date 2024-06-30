import os
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv
from handlers.start_handler import start
from handlers.button_handler import button
from handlers.field_handler import receive_field_value, AWAITING_FIELD

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AWAITING_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_field_value),
                             CallbackQueryHandler(button)],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
