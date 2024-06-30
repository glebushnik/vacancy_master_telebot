from telegram import Update
from telegram.ext import CallbackContext
from utils.helpers import request_next_field
from config.fields import FIELDS, AWAITING_FIELD


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
