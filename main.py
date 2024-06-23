import json
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, CallbackContext

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для обработки ввода текста после выбора кнопки
AWAITING_POSITION = 1
AWAITING_COMPANY_NAME = 2
AWAITING_CITY = 3
AWAITING_WORK_FORMAT = 4
AWAITING_PROJECT_SUBJECT = 5
AWAITING_PROJECT_THEME = 6
AWAITING_RESPONSIBILITY = 7
AWAITING_REQUIREMENTS = 8
AWAITING_CONTACTS = 9
AWAITING_TAGS = 10
AWAITING_APPROVAL = 11

# Словарь для хранения топиков и их идентификаторов
TOPICS = {
    "Основной топик": {"message_thread_id": None, "chat_id": "-1002241329040"},
    "Побочный топик": {"message_thread_id": "14", "chat_id": "-1002241329040_14"}
}

# Токен вашего бота
BOT_TOKEN = "7440529150:AAGn6-GVJHuZZAucSLXIXS5O1SZmj_kXZ5o"

# ID пользователя @glebushnik
REVIEWER_ID = 93281775
 # замените на реальный user_id

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

    # Приглашаем пользователя ввести текст сообщения
    await query.message.reply_text(f"Вы выбрали топик '{topic_name}'. Начнем создание объявления о вакансии.\n"
                                   "Введите название вакансии-позиции (обязательное поле, например, 'Backend Developer'):")

    # Устанавливаем состояние ожидания ввода названия вакансии-позиции
    context.user_data['current_state'] = AWAITING_POSITION
    return AWAITING_POSITION

async def process_job_posting(update: Update, context: CallbackContext) -> int:
    """Обрабатывает ввод пользователя по шагам для создания объявления о вакансии."""
    user_input = update.message.text.strip()
    current_state = context.user_data.get('current_state', AWAITING_POSITION)

    # Проверяем, что предыдущее состояние было успешно завершено
    if current_state == AWAITING_POSITION:
        if not user_input:
            await update.message.reply_text("Название вакансии-позиции не может быть пустым. Пожалуйста, введите еще раз, например, 'Frontend Developer':")
            return AWAITING_POSITION
        context.user_data['position'] = user_input
        await update.message.reply_text("Введите название компании (обязательное поле, например, 'AwesomeTech Inc.'):")
        context.user_data['current_state'] = AWAITING_COMPANY_NAME
        return AWAITING_COMPANY_NAME

    elif current_state == AWAITING_COMPANY_NAME:
        if not user_input:
            await update.message.reply_text("Название компании не может быть пустым. Пожалуйста, введите еще раз, например, 'AwesomeTech Inc.':")
            return AWAITING_COMPANY_NAME
        context.user_data['company_name'] = user_input
        await update.message.reply_text("Введите город и/или тайм-зону (обязательное поле, например, 'Москва, GMT+3'):")
        context.user_data['current_state'] = AWAITING_CITY
        return AWAITING_CITY

    elif current_state == AWAITING_CITY:
        if not user_input:
            await update.message.reply_text("Город и/или тайм-зона не могут быть пустыми. Пожалуйста, введите еще раз, например, 'Москва, GMT+3':")
            return AWAITING_CITY
        context.user_data['city'] = user_input
        await update.message.reply_text("Введите формат работы (обязательное поле, например, 'Удаленно полный рабочий день'):")
        context.user_data['current_state'] = AWAITING_WORK_FORMAT
        return AWAITING_WORK_FORMAT

    elif current_state == AWAITING_WORK_FORMAT:
        if not user_input:
            await update.message.reply_text("Формат работы не может быть пустым. Пожалуйста, введите еще раз, например, 'Удаленно полный рабочий день':")
            return AWAITING_WORK_FORMAT
        context.user_data['work_format'] = user_input
        await update.message.reply_text("Введите предметную область проекта (обязательное поле, например, 'Веб-разработка'):")
        context.user_data['current_state'] = AWAITING_PROJECT_SUBJECT
        return AWAITING_PROJECT_SUBJECT

    elif current_state == AWAITING_PROJECT_SUBJECT:
        if not user_input:
            await update.message.reply_text("Предметная область проекта не может быть пустой. Пожалуйста, введите еще раз, например, 'Веб-разработка':")
            return AWAITING_PROJECT_SUBJECT
        context.user_data['project_subject'] = user_input
        await update.message.reply_text("Введите тематику проекта (обязательное поле, например, 'Разработка интернет-магазина'):")
        context.user_data['current_state'] = AWAITING_PROJECT_THEME
        return AWAITING_PROJECT_THEME

    elif current_state == AWAITING_PROJECT_THEME:
        if not user_input:
            await update.message.reply_text("Тематика проекта не может быть пустой. Пожалуйста, введите еще раз, например, 'Разработка интернет-магазина':")
            return AWAITING_PROJECT_THEME
        context.user_data['project_theme'] = user_input
        await update.message.reply_text("Введите ключевую ответственность (обязательное поле, например, 'Разработка бэкенд-части'):")
        context.user_data['current_state'] = AWAITING_RESPONSIBILITY
        return AWAITING_RESPONSIBILITY

    elif current_state == AWAITING_RESPONSIBILITY:
        if not user_input:
            await update.message.reply_text("Ключевая ответственность не может быть пустой. Пожалуйста, введите еще раз, например, 'Разработка бэкенд-части':")
            return AWAITING_RESPONSIBILITY
        context.user_data['responsibility'] = user_input
        await update.message.reply_text("Введите требования (обязательное поле, например, 'Опыт работы от 2 лет, знание Python и Django'):")
        context.user_data['current_state'] = AWAITING_REQUIREMENTS
        return AWAITING_REQUIREMENTS

    elif current_state == AWAITING_REQUIREMENTS:
        if not user_input:
            await update.message.reply_text("Требования не могут быть пустыми. Пожалуйста, введите еще раз, например, 'Опыт работы от 2 лет, знание Python и Django':")
            return AWAITING_REQUIREMENTS
        context.user_data['requirements'] = user_input
        await update.message.reply_text("Введите контакты (обязательное поле, например, 'Телефон: +7-XXX-XXX-XX-XX, Email: hr@company.com'):")
        context.user_data['current_state'] = AWAITING_CONTACTS
        return AWAITING_CONTACTS

    elif current_state == AWAITING_CONTACTS:
        if not user_input:
            await update.message.reply_text("Контакты не могут быть пустыми. Пожалуйста, введите еще раз, например, 'Телефон: +7-XXX-XXX-XX-XX, Email: hr@company.com':")
            return AWAITING_CONTACTS
        context.user_data['contacts'] = user_input
        await update.message.reply_text("Введите теги поста (обязательное поле, каждый тег должен начинаться с символа '#', например, '#python #django #backend'):")
        context.user_data['current_state'] = AWAITING_TAGS
        return AWAITING_TAGS

    elif current_state == AWAITING_TAGS:
        if not user_input:
            await update.message.reply_text("Теги поста не могут быть пустыми. Пожалуйста, введите еще раз, каждый тег должен начинаться с символа '#', например, '#python #django #backend':")
            return AWAITING_TAGS
        # Проверяем, что все теги начинаются с символа '#'
        tags = user_input.split()
        for tag in tags:
            if not tag.startswith('#'):
                await update.message.reply_text("Каждый тег должен начинаться с символа '#'. Пожалуйста, введите теги еще раз, например, '#python #django #backend':")
                return AWAITING_TAGS
        context.user_data['tags'] = user_input

        # Конструируем сообщение
        message_text = "<b>Название вакансии-позиции:</b> {}\n".format(context.user_data['position'])
        message_text += "<b>Название компании:</b> {}\n".format(context.user_data['company_name'])
        message_text += "<b>Город и/или тайм-зона:</b> {}\n".format(context.user_data['city'])
        message_text += "<b>Формат работы:</b> {}\n".format(context.user_data['work_format'])
        message_text += "<b>Предметная область проекта:</b> {}\n".format(context.user_data['project_subject'])
        message_text += "<b>Тематика проекта:</b> {}\n".format(context.user_data['project_theme'])
        message_text += "<b>Ключевая ответственность:</b> {}\n".format(context.user_data['responsibility'])
        message_text += "<b>Требования:</b> {}\n".format(context.user_data['requirements'])
        message_text += "<b>Контакты:</b> {}\n".format(context.user_data['contacts'])
        message_text += "<b>Теги поста:</b> {}".format(context.user_data['tags'])

        # Отправляем сообщение на проверку к пользователю @glebushnik
        keyboard = [
            [
                InlineKeyboardButton("Опубликовать", callback_data="approve"),
                InlineKeyboardButton("Отклонить", callback_data="reject")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=REVIEWER_ID, text=message_text, reply_markup=reply_markup, parse_mode="HTML")

        # Устанавливаем состояние ожидания одобрения
        context.user_data['current_state'] = AWAITING_APPROVAL
        context.user_data['approval_message_text'] = message_text
        context.user_data['approval_message_id'] = update.message.message_id
        return AWAITING_APPROVAL

async def handle_approval(update: Update, context: CallbackContext) -> None:
    """Обрабатывает одобрение или отклонение сообщения."""
    query = update.callback_query
    await query.answer()

    decision = query.data
    approval_message_text = context.user_data.get('approval_message_text')
    approval_message_id = context.user_data.get('approval_message_id')
    original_message_id = approval_message_id

    # Получаем информацию о топике и чате
    topic_name = context.user_data['selected_topic']
    topic_info = TOPICS.get(topic_name)

    if not topic_info:
        await update.message.reply_text("Произошла ошибка при выборе топика.")
        return ConversationHandler.END

    message_thread_id = topic_info["message_thread_id"]
    chat_id = topic_info["chat_id"]

    if decision == "approve":
        data = {
            "chat_id": chat_id,
            "text": approval_message_text,
            "parse_mode": "HTML"
        }

        if message_thread_id:
            data["message_thread_id"] = message_thread_id

        # Отправляем сообщение через API Telegram
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            headers={"Content-Type": "application/json"},
            json=data
        )

        # Проверяем, что сообщение отправлено успешно
        if response.status_code == 200:
            await query.message.reply_text(f"Сообщение отправлено в {topic_name}.")
            await context.bot.send_message(chat_id=original_message_id, text="Ваше сообщение было опубликовано.")
        else:
            await query.message.reply_text("Произошла ошибка при отправке сообщения.")
            await context.bot.send_message(chat_id=original_message_id, text="Произошла ошибка при отправке вашего сообщения.")

    elif decision == "reject":
        await query.message.reply_text("Сообщение отклонено.")
        await context.bot.send_message(chat_id=original_message_id, text="Ваше сообщение было отклонено.")

    # Сбрасываем состояние
    del context.user_data['selected_topic']
    del context.user_data['current_state']
    del context.user_data['approval_message_text']
    del context.user_data['approval_message_id']
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

    # Добавляем обработчик ввода сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_job_posting))
    application.add_handler(CallbackQueryHandler(handle_approval))

    application.run_polling()

if __name__ == '__main__':
    main()
