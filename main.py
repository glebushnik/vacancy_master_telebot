import json
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext,
)

# Включаем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для обработки ввода текста после выбора кнопки
AWAITING_FIELD = 1

# Словарь для хранения полей вакансии и их обязательности
FIELDS = {
    "position": {
        "label": "Название вакансии-позиции",
        "required": 1,
        "example": "Системный аналитик на проект внедрения CRM",
    },
    "code": {"label": "Код вакансии", "required": 0, "example": "DAT-617"},
    "category": {"label": "Категория позиции", "required": 1, "example": "аналитик 1С"},
    "company_name": {"label": "Название компании", "required": 1, "example": "Ладома"},
    "company_url": {
        "label": "Сайт компании",
        "required": 0,
        "example": "https:/domen.ru/www.domen.ru/http://domen.ru/domen.ru/домен.рф",
    },
    "grade": {"label": "Грейд", "required": 0, "example": "Senior"},
    "location": {"label": "Локация", "required": 1, "example": "РФ"},
    "timezone": {"label": "Город и/или часовой пояс", "required": 1, "example": "Москва, +-2 часа"},
    "job_format": {"label": "Формат работы", "required": 1, "example": "Гибрид"},
    "subject_area": {"label": "Предметная область", "required": 0, "example": "финтех, e-commerce, ритейл"},
    "project_topic": {"label": "Тематика проекта", "required": 1, "example": "Разработка CRM системы"},
    "salary": {"label": "Зарплата", "required": 0, "example": "350.000₽"},
    "responsibility": {"label": "Ключевая зона ответственности", "required": 1, "example": "Разработка требований и проектирование интеграций"},
    "requirements": {"label": "Требования", "required": 1, "example": "Быть на связи 24/7"},
    "wishes": {"label": "Пожелания", "required": 0, "example": "Знание английского на уровне C1"},
    "tasks": {"label": "Рабочие задачи", "required": 0, "example": "Таски"},
    "bonus": {"label": "Бонусы", "required": 0, "example": "Бесплатный мерч"},
    "contacts": {"label": "Контакты", "required": 1, "example": "@telegramusername Иван Иванов"},
    "tags": {"label": "Теги", "required": 0, "example": "#интеграция, #B2B, #SaaS, #API"}
}

# Словарь для хранения топиков и их идентификаторов
TOPICS = {
    "Основной топик": {"message_thread_id": None, "chat_id": "-1002241329040"},
    "Побочный топик": {"message_thread_id": "14", "chat_id": "-1002241329040_14"},
}

# Токен вашего бота
BOT_TOKEN = "7272665628:AAHX2hQdwD2QGChr2IsdSgHvyv99J_YtGnc"


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
    """Обрабатывает нажатие кнопки с выбором топика, категории, грейда, локации или предметной области."""
    query = update.callback_query
    await query.answer()

    if context.user_data.get("current_field_index") is None:
        # Handle topic selection
        topic_name = query.data
        context.user_data["selected_topic"] = topic_name  # Сохраняем выбранный топик в данных пользователя

        # Инициализируем индекс текущего поля
        context.user_data["current_field_index"] = 0

        # Запрашиваем данные для первого поля
        await request_next_field(update, context)

    else:
        # Handle category, grade, location, or subject_area selection
        selected_value = query.data
        current_field = list(FIELDS.keys())[context.user_data["current_field_index"]]

        if current_field == "category":
            context.user_data["category"] = selected_value
        elif current_field == "grade":
            context.user_data["grade"] = selected_value
        elif current_field == "location":
            context.user_data["location"] = selected_value
        elif current_field == "job_format":
            context.user_data["job_format"] = selected_value
        elif current_field == "subject_area":
            if selected_value == "next":
                if len(context.user_data.get("subject_area", [])) < 3:
                    await query.message.reply_text(
                        "Необходимо выбрать как минимум 3 предметные области. Пожалуйста, выберите еще."
                    )
                    return

                # Move to the next field
                context.user_data["current_field_index"] += 1
                await request_next_field(update, context)
                return

            if "subject_area" not in context.user_data:
                context.user_data["subject_area"] = []
            if selected_value not in context.user_data["subject_area"]:
                context.user_data["subject_area"].append(selected_value)

            selected_areas = ", ".join(context.user_data["subject_area"])

            if len(context.user_data["subject_area"]) < 3:
                keyboard = [
                    [InlineKeyboardButton(area, callback_data=area)] for area in [
                        "финтех", "e-commerce", "ритейл", "логистика", "foodtech",
                        "edtech", "стройтех", "medtech", "госсистемы", "ERP",
                        "CRM", "traveltech", "авиация", "другая"
                    ] if area not in context.user_data["subject_area"]
                ] + [[InlineKeyboardButton("Перейти к следующему пункту", callback_data="next")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.message.reply_text(
                    f"Вы выбрали: {selected_areas}. Выберите еще одну область или перейдите к следующему пункту:",
                    reply_markup=reply_markup
                )
            else:
                await query.message.reply_text(
                    f"Вы выбрали: {selected_areas}. Переход к следующему пункту."
                )
                context.user_data["current_field_index"] += 1
                await request_next_field(update, context)
                return

        # Move to the next field (if any)
        if current_field != "subject_area":
            context.user_data["current_field_index"] += 1
            await request_next_field(update, context)


async def request_next_field(update: Update, context: CallbackContext) -> None:
    """Запрашивает у пользователя данные для следующего поля."""
    field_index = context.user_data.get("current_field_index", 0)
    field_keys = list(FIELDS.keys())

    if field_index < len(field_keys):
        field_key = field_keys[field_index]
        field_info = FIELDS[field_key]

        if update.message:
            await update.message.reply_text(
                f"Введите {field_info['label']} (пример: {field_info['example']}):"
            )
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                f"Введите {field_info['label']} (пример: {field_info['example']}):"
            )

        # Check if the current field is 'category', 'grade', 'location', or 'subject_area' to show options
        if field_key == "category":
            categories = [
                "аналитик 1С",
                "BI-аналитик",
                "аналитик данных",
                "продуктовый аналитик",
                "бизнес-аналитик",
                "аналитик бизнес-процессов",
                "системный аналитик",
                "system owner",
                "проектировщик ИТ-решений",
            ]
            keyboard = [
                [InlineKeyboardButton(category, callback_data=category)]
                for category in categories
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.message:
                await update.message.reply_text(
                    "Выберите категорию позиции:", reply_markup=reply_markup
                )
            elif update.callback_query:
                await update.callback_query.message.reply_text(
                    "Выберите категорию позиции:", reply_markup=reply_markup
                )

        elif field_key == "grade":
            grades = ["Junior", "Middle", "Senior", "Lead", "-"]
            keyboard = [
                [InlineKeyboardButton(grade, callback_data=grade)] for grade in grades
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.message:
                await update.message.reply_text("Выберите грейд:", reply_markup=reply_markup)
            elif update.callback_query:
                await update.callback_query.message.reply_text(
                    "Выберите грейд:", reply_markup=reply_markup
                )

        elif field_key == "location":
            locations = ["РФ", "Казахстан", "Беларусь", "Не важно", "Другая страна"]
            keyboard = [
                [InlineKeyboardButton(location, callback_data=location)] for location in locations
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.message:
                await update.message.reply_text("Выберите локацию:", reply_markup=reply_markup)
            elif update.callback_query:
                await update.callback_query.message.reply_text(
                    "Выберите локацию:", reply_markup=reply_markup
                )

        elif field_key == "job_format":
            formats = ["Удаленно", "Гибрид", "Офис"]
            keyboard = [
                [InlineKeyboardButton(job_format, callback_data=job_format)] for job_format in formats
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.message:
                await update.message.reply_text("Выберите формат работы:", reply_markup=reply_markup)
            elif update.callback_query:
                await update.callback_query.message.reply_text(
                    "Выберите формат работы:", reply_markup=reply_markup
                )

        elif field_key == "subject_area":
            subject_areas = [
                "финтех",
                "e-commerce",
                "ритейл",
                "логистика",
                "foodtech",
                "edtech",
                "стройтех",
                "medtech",
                "госсистемы",
                "ERP",
                "CRM",
                "traveltech",
                "авиация",
                "другая",
            ]
            keyboard = [
                [InlineKeyboardButton(area, callback_data=area)] for area in subject_areas
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.message:
                await update.message.reply_text(
                    "Выберите предметную область (до 3 вариантов):", reply_markup=reply_markup
                )
            elif update.callback_query:
                await update.callback_query.message.reply_text(
                    "Выберите предметную область (до 3 вариантов):", reply_markup=reply_markup
                )

    else:
        await finalize_post(update, context)


async def process_job_posting(update: Update, context: CallbackContext) -> int:
    """Обрабатывает ввод пользователя по шагам для создания объявления о вакансии."""
    user_input = update.message.text.strip()
    field_index = context.user_data.get("current_field_index", 0)
    field_keys = list(FIELDS.keys())

    if field_index < len(field_keys):
        field_key = field_keys[field_index]
        field_info = FIELDS[field_key]

        if field_key in ["category", "grade", "location", "job_format", "subject_area"]:
            # Store the selected category, grade, location, or subject_area from the callback data
            context.user_data[field_key] = user_input
            context.user_data["current_field_index"] += 1
            await request_next_field(update, context)
            return AWAITING_FIELD

        if field_info["required"] == 1 and not user_input:
            await update.message.reply_text(
                f"{field_info['label']} не может быть пустым. Пожалуйста, введите еще раз, например, '{field_info['example']}':"
            )
            return AWAITING_FIELD

        context.user_data[field_key] = user_input
        context.user_data["current_field_index"] += 1

        await request_next_field(update, context)
        return AWAITING_FIELD

    return ConversationHandler.END


async def finalize_post(update: Update, context: CallbackContext) -> None:
    """Формирует и отправляет сообщение в выбранный топик."""
    message_text = ""

    for field_key, field_info in FIELDS.items():
        field_value = context.user_data.get(field_key, "")
        if field_value:
            if isinstance(field_value, list):
                field_value = ", ".join(field_value)
            message_text += f"<b>{field_info['label']}:</b> {field_value}\n"

    # Формируем данные для отправки сообщения
    topic_name = context.user_data["selected_topic"]
    topic_info = TOPICS.get(topic_name)

    if not topic_info:
        await update.message.reply_text("Произошла ошибка при выборе топика.")
        return

    message_thread_id = topic_info["message_thread_id"]
    chat_id = topic_info["chat_id"]

    data = {
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "HTML",
    }

    if message_thread_id:
        data["message_thread_id"] = message_thread_id

    # Отправляем сообщение через API Telegram
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        headers={"Content-Type": "application/json"},
        json=data,
    )

    # Проверяем, что сообщение отправлено успешно
    if response.status_code == 200:
        if update.message:
            await update.message.reply_text(f"Сообщение отправлено в {topic_name}.")
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                f"Сообщение отправлено в {topic_name}."
            )
    else:
        if update.message:
            await update.message.reply_text("Произошла ошибка при отправке сообщения.")
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                "Произошла ошибка при отправке сообщения."
            )

    # Сбрасываем состояние
    context.user_data.clear()


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
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, process_job_posting)],
        states={
            AWAITING_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_job_posting)]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
