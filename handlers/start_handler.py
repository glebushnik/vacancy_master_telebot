from telegram import Update
from telegram.ext import CallbackContext
from utils.helpers import request_next_field

async def start(update: Update, context: CallbackContext) -> int:
    context.user_data["current_field_index"] = 0
    context.user_data["selected_subject_areas"] = []
    return await request_next_field(update, context)
