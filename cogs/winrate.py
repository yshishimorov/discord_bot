import requests
import disnake
from datetime import datetime, timedelta
from pathlib import Path
from disnake import ui
from disnake.ext import commands, tasks
from config import API_KEY
import config

headers = {
    "x-api-key": API_KEY,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

project_root = Path(__file__).resolve().parent.parent
images_path = project_root / "images"

class WinrateMemphis(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.processed_match_ids = set() # Айди(API) уже обработанных каптов
        self.check_api_loop.start() # Запуск задачи на фоне при старте

    # Останавливаем задачу, если ког выгружается
    def cog_unload(self): 
        self.check_api_loop.cancel()

    @tasks.loop(seconds=60)
    async def check_api_loop(self):
        await self.bot.wait_until_ready() # Ждем полной загрузки бота

        # Перебираем данные для запроса
        for conf in config.CONFIGS:
            await self.process_api_data(conf)

    # Размещение первой строки сообщения по центру
    def centered_title(self, attackers_name, defenders_name):
        max_len = 14
        left_name = attackers_name.rjust(max_len)
        right_name = defenders_name.ljust(max_len)
        return (f'# `⚔️`  {left_name}  VS  {right_name}  `🛡️`')

    async def process_api_data(self, conf):
        url = conf["url"]
        current_id = conf["id"]
        server_name = conf["server_name"]

        # Проверка канала
        try:
            channel = await self.bot.fetch_channel(config.WINRATE_CHANNEL_ID)
        except disnake.NotFound:
            print(f'Канал с айди {config.WINRATE_CHANNEL_ID} не существует.')
            return
        except disnake.Forbidden:
            print(f'У бота нет прав на просмотр канала {config.WINRATE_CHANNEL_ID}.')
            return
        except Exception as e:
            print(f'Ошибка при поиске канала: {e}')
            return

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                match_result = data.get('result')
                captures = match_result.get('captures')

                for capt in captures:
                    id = str(capt.get("id")) # Айди матча в API, не капта

                    if id not in self.processed_match_ids:
                        all_players = []
                        self.processed_match_ids.add(id)
                        attackers_id = str(capt.get("attackersId"))
                        defenders_id = str(capt.get("defendersId"))
                
                        if attackers_id == current_id or defenders_id == current_id:
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

                            capt_result = 'Победа' if winner == current_id else 'Поражение'
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
                                if str(family_id) == current_id:
                                    for player in players_list:
                                        all_players.append(player)
                                        p_id = player.get("id")
                                        p_name = player.get("name")
                                        p_familyName = player.get("familyName")
                                        p_damage = player.get("damage")
                                        p_kills = player.get("kills")
                                        p_familyId = str(player.get('familyId'))

                            # Формирование списка игроков по количеству убуийств
                            top_kills = sorted(all_players, key=lambda x: (x.get("kills", 0), x.get("damage", 0)), reverse=True)
                            top_kills_list = []
                            for i, p in enumerate(top_kills, 1):
                                line = f"{i}. {p.get('name')} #{p.get('id')} — {p.get('kills')} убийств {p.get('damage')} урона"
                                top_kills_list.append(line)

                            file_name = config.MAP_IMAGES.get(selected_map_name) 
                            file_to_send = None
                            attachment_url = None

                            # Проверка файла
                            if file_name and (images_path / file_name).exists():
                                file_to_send = disnake.File(images_path / file_name, filename=file_name)
                                attachment_url = f"attachment://{file_name}"
                            else:
                                print(f"Изображение не найдено. Поиск в папке: {images_path.absolute()}")

                            title_text = self.centered_title(attackers_name, defenders_name) # Текст заголовка

                            # Формирование и отправка сообщения
                            await channel.send(
                                file=file_to_send, 
                                components=[                 
                                    ui.Container(
                                        # Если переменные будут None то сообщение бещопасно отправится
                                        *( [ui.MediaGallery(disnake.MediaGalleryItem(attachment_url))] if attachment_url else [] ),
                                        ui.TextDisplay(title_text),
                                        ui.TextDisplay(f'-# *{attackers_kills} убийств, {attackers_damage} урона, {attackers_count} игроков              {defenders_kills} убийств, {defenders_damage} урона, {defenders_count} игроков*'),
                                        ui.Separator(divider=False),
                                        ui.Separator(divider=False),
                                        ui.Separator(divider=True),
                                        ui.Separator(divider=False),
                                        ui.Separator(divider=False),
                                        ui.TextDisplay(f'• **`🏆` Исход:** {capt_result}'), 
                                        ui.TextDisplay(f'• **`🗺️` Карта:** {selected_map_name}'), 
                                        ui.TextDisplay(f'• **`🌐` Сервер:** {server_name}'),
                                        ui.TextDisplay(f'• **`🗓️` Дата:** {date}'),
                                        ui.TextDisplay(f'• **`🕐` Время начала:** {start_time}'),
                                        accent_colour=disnake.Colour.green() if capt_result == 'Победа' else disnake.Colour.red()
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
    bot.add_cog(WinrateMemphis(bot))
