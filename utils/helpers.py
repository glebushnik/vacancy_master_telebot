import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext, ConversationHandler
from config.fields import FIELDS, AWAITING_FIELD
from config.channels import CHANNEL
from config.logger import logger
import requests
import pymongo
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

db_client_uri = os.getenv("DB_CLIENT_URI")
db_name = os.getenv("DB_NAME")
db_collection_name = os.getenv("DB_COLLECTION_NAME")



client = pymongo.MongoClient(db_client_uri)
db = client[db_name]
collection = db[db_collection_name]

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

        existing_message = collection.find_one({"description": message_text})
        if existing_message:
            logger.info("Такая вакансия уже существует")

            reply_markup = ReplyKeyboardMarkup(
                [[KeyboardButton('/start')]],
                one_time_keyboard=True,
                resize_keyboard=True
            )

            await update.message.reply_text(
                "Такая вакансия уже есть! Нажмите кнопку ниже, чтобы создать новую вакансию.",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
        else:
            message_data = {"description": message_text}
            collection.insert_one(message_data)
            logger.info("Анкета сохранена.")

            await update.message.reply_text(
                f"Ваша анкета:\n\n{message_text}\n\nАнкета отправлена в чат: t.me/{chat_id_without_at}/{channel['message_thread_id']}"
            )

            # Отправка данных в указанные топики
            await send_vacancy_data(context)

            reply_markup = ReplyKeyboardMarkup(
                [[KeyboardButton('/start')]],
                one_time_keyboard=True,
                resize_keyboard=True
            )

            await update.message.reply_text(
                "Нажмите кнопку ниже, чтобы создать новую вакансию",
                reply_markup=reply_markup
            )
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
    location = vacancy_data.get("location", "")

    if category == 'аналитик 1С': channel = CHANNEL["Analystic_job"]
    elif category in ["BI-аналитик","аналитик данных","продуктовый аналитик"]: channel = CHANNEL["Data_Analysis_job"]
    elif category in [
        "бизнес-аналитик",
        "аналитик бизнес-процессов",
        "системный аналитик",
        "system owner",
        "проектировщик ИТ-решений",
    ] and "финтех" in subject_area and location == "РФ":
        channel = CHANNEL["Analyst_job_fintech"]
    elif category in [
        "бизнес-аналитик",
        "аналитик бизнес-процессов",
        "системный аналитик",
        "system owner",
        "проектировщик ИТ-решений",
    ] and subject_area in ["e-commerce", "ритейл", "логистика"] and location == "РФ":
        channel = CHANNEL["Analyst_job_retail"]
    elif category in [
        "бизнес-аналитик",
        "аналитик бизнес-процессов",
        "системный аналитик",
        "system owner",
        "проектировщик ИТ-решений",
    ] and location == "РФ":
        channel = CHANNEL["Analyst_job_other"]
    else:
        channel = CHANNEL["Analyst_job_other_countries"]

    chat_id = channel["chat_id"]
    message_text = "\n".join(
        [f"{FIELDS[key]['label']}: {value}" for key, value in vacancy_data.items() if key in FIELDS])

    message_thread_id = channel["message_thread_id"]

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