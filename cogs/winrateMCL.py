import requests
import disnake
from datetime import datetime, timedelta
from pathlib import Path
from disnake import ui
from disnake.ext import commands, tasks
from config import API_KEY

FARADAY_ID = '6'
CHANNEL_ID = 1549792168212963348
URL = "https://api.majestic-files.net/v1/ext/family-wars/MCL"

project_root = Path(__file__).resolve().parent.parent
# images_path = project_root / "images"

headers = {
    "x-api-key": API_KEY,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# MAP_IMAGES = {
#     "завод": "factory.webp",
#     "порт": "port.webp",
# }

class WinrateMCL(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.faraday_id = FARADAY_ID
        self.processed_match_ids = set() # Айди уже обработанных каптов

        self.check_api_loop.start() # Запуск задачи на фоне при старте

    def cog_unload(self): # Останавливаем задачу, если ког выгружается
        self.check_api_loop.cancel()

    @tasks.loop(seconds=60)
    async def check_api_loop(self):

        await self.bot.wait_until_ready() # Ждем полной загрузки бота

        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel:
            print(f'Канал с айди {CHANNEL_ID} не найден.')
            return

        try:
            response = requests.get(URL, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                captures = result.get('captures')

                for capt in captures:
                    id = str(capt.get("id")) # Айди матча в API, не капта

                    if id not in self.processed_match_ids:
                        all_players = []
                        self.processed_match_ids.add(id)
                        attackers_id = str(capt.get("attackersId"))
                        defenders_id = str(capt.get("defendersId"))
                
                        if attackers_id == self.faraday_id or defenders_id == self.faraday_id:
                            attackers_name = str(capt.get("attackersName"))
                            defenders_name = str(capt.get("defendersName"))
                            attackers_id = str(capt.get("attackersId"))
                            defenders_id = str(capt.get("defendersId"))
                            winner = str(capt.get('winner'))

                            selected_map_name = capt.get("selectedMapName")
                            players_dict = capt.get("players")
                            capt_id = capt.get('captureId')

                            # Время и дата в формате UTC+3
                            utc_time = datetime.fromisoformat(capt.get("startAt").replace("Z", "+00:00"))
                            msk_time = utc_time + timedelta(hours=3) 
                            start_time = msk_time.strftime("%H:%M") 
                            date = msk_time.strftime("%d.%m.%Y") 

                            result = 'Победа' if winner == self.faraday_id else 'Поражение'
                            enemy = defenders_name if attackers_name.lower() == 'faraday' else attackers_name

                            attackers_kills = 0
                            defenders_kills = 0
                            attackers_damage = 0
                            defenders_damage = 0
                            attackers_count = 0
                            defenders_count = 0

                            for family_id, players_list in players_dict.items():
                                total_family_kills = sum(p.get("kills") for p in players_list)
                                total_family_damage = sum(p.get("damage") for p in players_list)

                                if str(family_id) == attackers_id:
                                    attackers_kills = total_family_kills
                                    attackers_damage = total_family_damage
                                    attackers_count = len(players_list)
                                else:
                                    defenders_kills = total_family_kills
                                    defenders_damage = total_family_damage
                                    defenders_count = len(players_list)

                                # Статистика каждого игрока из семьи
                                if family_id == self.faraday_id:
                                    for player in players_list:
                                        all_players.append(player)
                                        p_id = player.get("id")
                                        p_name = player.get("name")
                                        p_familyName = player.get("familyName")
                                        p_damage = player.get("damage")
                                        p_kills = player.get("kills")
                                        p_familyId = str(player.get('familyId'))

                            # Формирование списка игроков по количеству убуийств
                            top_kills = sorted(all_players, key=lambda x: x.get("kills"), reverse=True)
                            top_kills_list = []
                            for i, p in enumerate(top_kills, 1):
                                line = f"{i}. {p.get('name')} #{p.get('id')} — {p.get('kills')} убийств {p.get('damage')} урона"
                                top_kills_list.append(line)

                            # file_to_send = disnake.File(images_path / 'sandy.webp', filename="sandy.webp")
                            # attachment_url = "attachment://sandy.webp"

                            # Отправка сообщения
                            channel = self.bot.get_channel(CHANNEL_ID)
                            await channel.send(
                                # file=file_to_send, 
                                components=[                 
                                    ui.Container(
                                        # ui.MediaGallery(disnake.MediaGalleryItem(attachment_url)),
                                        ui.TextDisplay(f'# `⚔️`  {attackers_name}    VS    {defenders_name}  `🛡️`'),
                                        ui.TextDisplay(f'-# *{attackers_kills} убийств, {attackers_damage} урона, {attackers_count} игроков              {defenders_kills} убийств, {defenders_damage} урона, {defenders_count} игроков*'),
                                        ui.Separator(divider=False),
                                        ui.Separator(divider=False),
                                        ui.Separator(divider=True),
                                        ui.Separator(divider=False),
                                        ui.Separator(divider=False),
                                        ui.TextDisplay(f'• **`🏆` Исход:** {result}'), 
                                        ui.TextDisplay(f'• **`🗺️` Карта:** {selected_map_name}'), 
                                        ui.TextDisplay(f'• **`🌐` Сервер:** MCL'),
                                        ui.TextDisplay(f'• **`🗓️` Дата:** {date}'),
                                        ui.TextDisplay(f'• **`🕐` Время начала:** {start_time}'),
                                        accent_colour=disnake.Colour.green() if result == 'Победа' else disnake.Colour.red()
                                    ),

                                    ui.Container(
                                        ui.TextDisplay('# `📄` Список игроков'),
                                        ui.TextDisplay(f'```{"\n".join(top_kills_list)}```')
                                    )
                                ]
                            )

            else:
                print(f'Ошибка API. Статус: {response.status_code}')

        except requests.exceptions.Timeout:
            print("Превышено время ожидания ответа от API.")

        except requests.exceptions.RequestException as e:
            print(f'Проблема с подключением к API: {e}')

def setup(bot: commands.Bot):
    bot.add_cog(WinrateMCL(bot))
