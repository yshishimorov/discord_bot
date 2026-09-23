import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
PREFIX = "!"
API_KEY = os.getenv("API_KEY")
COLOR_MAIN = 0x3498db  # Синий цвет для основных эмбедов
COLOR_ERROR = 0xe74c3c # Красный цвет для ошибок