from config import *
from TelegramBot import *

telegram_bot = TelegramBot(BOT_API_TOKEN, CHAT_GPT_LIST, DATABASE,
                           NAME_BOT_COMMAND)