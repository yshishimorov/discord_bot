import disnake
from disnake.ext import commands, tasks
import requests
from datetime import datetime

URL = "https://api.majestic-files.net/v1/ext/family-wars/RU19"
KEY = "idURS2Fwm9oVdxu9ihlsbAFTOUaLHUT8dZ"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
FARADAY_ID = '20'
CHANNEL_ID = 1549792168212963348

headers = {
    "x-api-key": KEY,
    "User-Agent": UA
}

class CaptWinrate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.faraday_id = FARADAY_ID
        self.processed_match_ids = set() 

        self.check_api_loop.start() # Запуск задачи на фоне при старте

    def cog_unload(self): # Останавливаем задачу, если ког выгружается
        self.check_api_loop.cancel()

    @tasks.loop(seconds=60)
    async def check_api_loop(self):
        try:
            response = requests.get(URL, headers=headers)

            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                captures = result.get('captures')

                for capt in captures:
                    id = str(capt.get("id"))

                    if id not in self.processed_match_ids:
                        self.processed_match_ids.add(id)
                        all_players = []
                        attackers_id = str(capt.get("attackersId"))
                        defenders_id = str(capt.get("defendersId"))
                    
                        if attackers_id == self.faraday_id or defenders_id == self.faraday_id:
                            capt_id = capt.get('captureId')
                            attackers_name = str(capt.get("attackersName"))
                            defenders_name = str(capt.get("defendersName"))
                            attackers_id = str(capt.get("attackersId"))
                            defenders_id = str(capt.get("defendersId"))
                            winner = str(capt.get('winner'))
                            end_time = datetime.fromisoformat(capt.get("endAt").replace("Z", "+00:00")).strftime("%d.%m.%Y. %H:%M")
                            selected_map_name = capt.get("selectedMapName")
                            players_dict = capt.get("players")
                            result = 'Победа' if winner == self.faraday_id else 'Поражение'
                            enemy = defenders_name if attackers_name.lower() == 'faraday' else attackers_name

                            attackers_kills = 0
                            defenders_kills = 0
                            attackers_damage = 0
                            defenders_damage = 0

                            for family_id, players_list in players_dict.items():
                                total_family_kills = sum(p.get("kills") for p in players_list)
                                total_family_damage = sum(p.get("damage") for p in players_list)

                                if str(family_id) == attackers_id:
                                    attackers_kills = total_family_kills
                                    attackers_damage = total_family_damage
                                elif str(family_id) == defenders_id:
                                    defenders_kills = total_family_kills
                                    defenders_damage = total_family_damage

                                if family_id == self.faraday_id:
                                    for player in players_list:
                                        all_players.append(player)
                                        p_id = player.get("id")
                                        p_name = player.get("name")
                                        p_familyName = player.get("familyName")
                                        p_damage = player.get("damage")
                                        p_kills = player.get("kills")
                                        p_familyId = str(player.get('familyId'))

                            top_damage = sorted(all_players, key=lambda x: x.get("damage"), reverse=True)[:5]
                            top_kills = sorted(all_players, key=lambda x: x.get("kills"), reverse=True)[:5]

                            top_kills_list = []
                            for i, p in enumerate(top_kills, 1):
                                line = f"{i}. {p.get('name')} #{p.get('id')} — {p.get('kills')} убийств"
                                top_kills_list.append(line)

                            top_damage_list = []
                            for i, p in enumerate(top_damage, 1):
                                line = f"{i}. {p.get('name')} #{p.get('id')} — {p.get('damage')} урона"
                                top_damage_list.append(line)

                            channel = self.bot.get_channel(CHANNEL_ID)
                            embed = disnake.Embed(
                                title=f"⚔️ {attackers_name} VS {defenders_name} 🛡️",
                                color=disnake.Color.green() if winner == self.faraday_id else disnake.Color.red(),
                                description=f"*{attackers_kills} убийств, {attackers_damage} урона   |   {defenders_kills} убийств, {defenders_damage} урона*"
                            )

                            embed.add_field(name="Карта:", value=selected_map_name, inline=True) 
                            embed.add_field(name="Исход:", value=result, inline=True) 
                            embed.add_field(name="ID капта:", value=capt_id, inline=True) 
                            embed.add_field(name="ТОП-5 по убийствам:", value="\n".join(top_kills_list), inline=True)
                            embed.add_field(name="ТОП-5 по урону:", value="\n".join(top_damage_list), inline=True)
                            embed.set_thumbnail(url='https://colt.family/uploads/servers/srv_1787421357047_qugdvp.png')
                            embed.set_footer(text=end_time)
                            await channel.send(embed=embed)

            else:
                print(response.status_code)

        except Exception as e:
            print(e)

    @check_api_loop.before_loop
    async def before_check_api_loop(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(CaptWinrate(bot))
