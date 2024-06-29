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
CONFIRMATION = 2
EDIT_FIELD = 3

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
    "subject_area": {"label": "Предметная область", "required": 1, "example": ""},
    "job_format": {"label": "Формат работы", "required": 1, "example": "Гибрид"},
    "project_group": {"label": "Тематика проекта", "required": 1, "example": ""},
    "salary": {"label": "Зарплата", "required": 0, "example": "100.000₽"},
    "responsibilities": {"label": "Ключевая зона ответственности", "required": 1,
                         "example": "Разработка требований и проектирование интеграций"},
    "requirements": {"label": "Требования", "required": 1, "example": "Быть онлайн 24/7"},
    "tasks": {"label": "Рабочие задачи", "required": 0, "example": "Рабочие задачи"},
    "wishes": {"label": "Пожелания", "required": 0, "example": "Знание английского на уровне C1"},
    "bonus": {"label": "Бонусы", "required": 0, "example": "Мерч"},
    "contacts": {"label": "Контакты", "required": 1, "example": "@telegramuser Ivan Ivanov, CEO"},
    "tags": {"label": "Теги", "required": 0, "example": "#интеграция, #B2B, #SaaS, #API"}
}

# Словарь для хранения топиков и их идентификаторов
CHANNEL = {
    "Analystic_job": {"message_thread_id": None, "chat_id": "@analyst1c_job"},
    "Data_Analysis_job": {"message_thread_id": None, "chat_id": "@data_analysis_jobs"},
    "Analyst_job_fintech": {"message_thread_id": "76814", "chat_id": "@analyst_job"},
    "Analyst_job_retail": {"message_thread_id": "81463", "chat_id": "@analyst_job"},
    "Analyst_job_other": {"message_thread_id": "63901", "chat_id": "@analyst_job"},
    "Analyst_job_other_countries": {"message_thread_id": "63909", "chat_id": "@analyst_job"},
}

# Токен вашего бота
BOT_TOKEN = "7272665628:AAHX2hQdwD2QGChr2IsdSgHvyv99J_YtGnc"

async def start(update: Update, context: CallbackContext) -> int:
    """Отправляет сообщение при вводе команды /start и сразу начинает анкету."""
    context.user_data["current_field_index"] = 0
    context.user_data["selected_subject_areas"] = []
    return await request_next_field(update, context)

async def button(update: Update, context: CallbackContext) -> int:
    """Обрабатывает нажатие кнопки с выбором категории, грейда, локации или предметной области."""
    query = update.callback_query
    await query.answer()

    selected_value = query.data
    current_field = list(FIELDS.keys())[context.user_data["current_field_index"]]

    if current_field == "category":
        context.user_data["category"] = selected_value
    elif current_field == "grade":
        context.user_data["grade"] = selected_value
    elif current_field == "location":
        context.user_data["location"] = selected_value
    elif current_field == "subject_area":
        if selected_value == "Следующий пункт анкеты":
            if len(context.user_data["selected_subject_areas"]) == 0:
                await update.callback_query.message.reply_text(
                    "Пожалуйста, выберите хотя бы одну предметную область."
                )
                return AWAITING_FIELD
            context.user_data["subject_area"] = ", ".join(context.user_data["selected_subject_areas"])
            context.user_data["current_field_index"] += 1
            return await request_next_field(update, context)
        else:
            if selected_value not in context.user_data["selected_subject_areas"]:
                if len(context.user_data["selected_subject_areas"]) < 3:
                    context.user_data["selected_subject_areas"].append(selected_value)
                    selected_subject_areas = ", ".join(context.user_data["selected_subject_areas"])
                    await update.callback_query.message.reply_text(
                        f"Выбранные предметные области: {selected_subject_areas}"
                    )
                else:
                    await update.callback_query.message.reply_text(
                        "Вы не можете выбрать более 3 предметных областей."
                    )
                    return AWAITING_FIELD

    # Переход к следующему полю только если не выбран "subject_area"
    if current_field != "subject_area":
        context.user_data["current_field_index"] += 1
        return await request_next_field(update, context)

    return AWAITING_FIELD


async def request_next_field(update: Update, context: CallbackContext) -> int:
    """Запрашивает у пользователя данные для следующего поля."""
    field_index = context.user_data.get("current_field_index", 0)
    field_keys = list(FIELDS.keys())

    if field_index < len(field_keys):
        field_key = field_keys[field_index]
        field_info = FIELDS[field_key]

        if update.message:
            await update.message.reply_text(
                f"Заполните поле '{field_info['label']}' (Например: {field_info['example']}):"
            )
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                f"Заполните поле '{field_info['label']}' (Например: {field_info['example']}):"
            )

        # Check if the current field is 'category', 'grade', 'location' or 'subject_area' to show options
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
            locations = ["РФ", "Казахстан", "Беларусь", "Не важно"]
            keyboard = [
                [InlineKeyboardButton(location, callback_data=location)]
                for location in locations
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.message:
                await update.message.reply_text("Выберите локацию:", reply_markup=reply_markup)
            elif update.callback_query:
                await update.callback_query.message.reply_text(
                    "Выберите локацию:", reply_markup=reply_markup
                )

        elif field_key == "subject_area":
            subject_areas = [
                "финтех",
                "риск-менеджмент",
                "дата сайнс/машинное обучение",
                "дата-инженерия",
                "маркетинг/CRM",
                "E-commerce",
                "биллинговые системы",
                "мобильная разработка",
                "геймдев",
                "WEB",
                "другое",
                "Следующий пункт анкеты",
            ]
            keyboard = [
                [InlineKeyboardButton(area, callback_data=area)]
                for area in subject_areas
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.message:
                await update.message.reply_text(
                    "Выберите предметную область (можно выбрать до 3):", reply_markup=reply_markup
                )
            elif update.callback_query:
                await update.callback_query.message.reply_text(
                    "Выберите предметную область (можно выбрать до 3):", reply_markup=reply_markup
                )

        return AWAITING_FIELD
    else:
        vacancy_data = context.user_data
        category = vacancy_data.get("category", "").lower()
        subject_area = vacancy_data.get("subject_area", "").lower()

        if category in [
            "бизнес-аналитик",
            "аналитик бизнес-процессов",
            "системный аналитик",
            "system owner",
            "проектировщик ИТ-решений",
        ] and "финтех" in subject_area:
            channel = CHANNEL["Analyst_job_fintech"]
        else:
            channel = CHANNEL["Analyst_job_other"]

        message_text = "\n".join([f"{FIELDS[key]['label']}: {value}" for key, value in vacancy_data.items() if key in FIELDS])
        chat_id_without_at = channel['chat_id'].replace("@", "")
        await update.message.reply_text(
            f"Ваша анкета:\n\n{message_text}\n\nАнкета отправлена в чат: t.me/{chat_id_without_at}/{channel['message_thread_id']}"
        )

        # Отправка данных в указанные топики
        await send_vacancy_data(context)
        return ConversationHandler.END

async def receive_field_value(update: Update, context: CallbackContext) -> int:
    """Получает значение поля от пользователя и сохраняет его в контексте."""
    field_index = context.user_data.get("current_field_index", 0)
    field_keys = list(FIELDS.keys())

    if field_index < len(field_keys):
        field_key = field_keys[field_index]
        user_input = update.message.text

        # Сохраняем значение поля в user_data
        context.user_data[field_key] = user_input
        context.user_data["current_field_index"] += 1

        return await request_next_field(update, context)

    return ConversationHandler.END

async def send_vacancy_data(context: CallbackContext) -> None:
    """Отправляет данные о вакансии в соответствующие топики на основе логики."""
    vacancy_data = context.user_data
    category = vacancy_data.get("category", "").lower()
    subject_area = vacancy_data.get("subject_area", "").lower()

    if category in [
        "бизнес-аналитик",
        "аналитик бизнес-процессов",
        "системный аналитик",
        "system owner",
        "проектировщик ИТ-решений",
    ] and "финтех" in subject_area:
        channel = CHANNEL["Analyst_job_fintech"]
    else:
        channel = CHANNEL["Analyst_job_other"]

    chat_id = channel["chat_id"]
    message_thread_id = channel["message_thread_id"]
    message_text = "\n".join([f"{FIELDS[key]['label']}: {value}" for key, value in vacancy_data.items() if key in FIELDS])

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message_text,
        "message_thread_id": message_thread_id
    }

    response = requests.post(url, data=data)
    if response.status_code == 200:
        logger.info("Вакансия успешно отправлена в топик.")
    else:
        logger.error(f"Ошибка при отправке вакансии: {response.text}")

def main() -> None:
    """Запуск бота."""
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
