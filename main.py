import json
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

AWAITING_MESSAGE = 1

TOPICS = {
    "Основной топик": {"message_thread_id": None, "chat_id": "-1002241329040"},
    "Побочный топик": {"message_thread_id": "14", "chat_id": "-1002241329040_14"}
}

BOT_TOKEN = "7440529150:AAGn6-GVJHuZZAucSLXIXS5O1SZmj_kXZ5o"

async def start(update: Update, context: CallbackContext) -> None:
    """Отправляет сообщение при вводе команды /start."""
    keyboard = [
        [InlineKeyboardButton(topic_name, callback_data=topic_name)] for topic_name in TOPICS
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Выберите топик для отправки сообщения:", reply_markup=reply_markup
    )

async def button(update: Update, context: CallbackContext) -> None:
    """Обрабатывает нажатие кнопки с выбором топика."""
    query = update.callback_query
    await query.answer()

    topic_name = query.data
    context.user_data['selected_topic'] = topic_name  # Сохраняем выбранный топик в данных пользователя

    await query.message.reply_text(f"Вы выбрали топик '{topic_name}'. Теперь введите текст сообщения:")

    return AWAITING_MESSAGE

async def message_handler(update: Update, context: CallbackContext) -> None:
    """Обрабатывает введенный пользователем текст."""
    user_message = update.message.text

    if 'selected_topic' not in context.user_data:
        await update.message.reply_text("Сначала выберите топик кнопкой.")
        return

    topic_name = context.user_data['selected_topic']
    topic_info = TOPICS.get(topic_name)

    if not topic_info:
        await update.message.reply_text("Произошла ошибка при выборе топика.")
        return

    message_thread_id = topic_info["message_thread_id"]
    chat_id = topic_info["chat_id"]

    data = {
        "chat_id": chat_id,
        "text": user_message
    }

    if message_thread_id:
        data["message_thread_id"] = message_thread_id

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        headers={"Content-Type": "application/json"},
        json=data
    )

    if response.status_code == 200:
        await update.message.reply_text(f"Сообщение отправлено в {topic_name}.")
    else:
        await update.message.reply_text("Произошла ошибка при отправке сообщения.")

    del context.user_data['selected_topic']
    return ConversationHandler.END

async def help_command(update: Update, context: CallbackContext) -> None:
    """Отправляет сообщение при вводе команды /help."""
    await update.message.reply_text("Используйте /start для начала.")

def main() -> None:
    """Запуск бота."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    application.run_polling()

if __name__ == '__main__':
    main()
