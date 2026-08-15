import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
PREFIX = "!"
COLOR_MAIN = 0x3498db  # Синий цвет для основных эмбедов
COLOR_ERROR = 0xe74c3c # Красный цвет для ошибок