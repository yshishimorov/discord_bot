import os
from dotenv import load_dotenv

load_dotenv()

PREFIX = "!"
TOKEN = os.getenv('BOT_TOKEN')
API_KEY = os.getenv('API_KEY')
WINRATE_CHANNEL_ID = 1549792168212963348

MAP_IMAGES = {
    "Церковь": 'cercov.webp',
    "Ферма": 'ferm.webp',
    "Миррор-Парк": 'mirror.webp',
    "Муравейник": 'muraveinik.webp',
    "Особняк": 'osobnyak.webp',
    "Палето-Бей": 'paleto.webp',
    "Пирс": 'pirc.webp',
    "Порт": 'port.webp',
    "Рокфорд": 'rockford.webp',
    "Сэнди-Шорс": 'sandy.webp',
    "Стройка «Ребл»": 'stroyka.webp',
    "Тату-салон": 'tatu-salon',
    "Ветряная ферма": 'vetryaki.webp',
    "Завод": 'zavod.webp'
}

CONFIGS = [
    {
        "id": "20",
        "url": "https://api.majestic-files.net/v1/ext/family-wars/RU19",
        "server_name": "Memphis"
    },
    {
        "id": "6",
        "url": "https://api.majestic-files.net/v1/ext/family-wars/MCL",
        "server_name": "MCL"
    }
]