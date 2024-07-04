from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from utils.helpers import request_next_field
from config.fields import FIELDS

AWAITING_FIELD = 1

async def receive_field_value(update: Update, context: CallbackContext) -> int:

    field_index = context.user_data.get("current_field_index", 0)
    field_keys = list(FIELDS.keys())

    if field_index < len(field_keys):
        field_key = field_keys[field_index]
        user_input = update.message.text

        context.user_data[field_key] = user_input
        context.user_data["current_field_index"] += 1

        return await request_next_field(update, context)

    return ConversationHandler.END
