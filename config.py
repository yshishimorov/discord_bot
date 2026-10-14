import os
from dotenv import load_dotenv

load_dotenv()

PREFIX = "!"
TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")