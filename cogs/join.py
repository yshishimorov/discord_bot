import disnake
from disnake.ext import commands
import datetime

PRIMARY_SERVER_ID = 1536873302142877746
LOG_CHANNEL_ID = 1538662630103842888

# Словарь с серверами
SECONDARY_SERVERS = [
    {
        "name": "FARADAY",
        "guild_id": 1538583246890082374,
        "required_roles": [1538583302779437136], # junior
        "given_role_id": 1538585904854077531
    }, 
    {
        "name": "ALLIANCE",
        "guild_id": 1538595490432679976,
        "required_roles": [1538595542609825923], # test
        "given_role_id": 1538664893102956575
    }
]

class RoleChecker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        if member.guild.id != PRIMARY_SERVER_ID:
            return

        results = []
        has_any_valid_role = False  # Нашел ли бот хотя бы одну нужную роль

        # Проверка нужных ролей на серверах из словаря
        for config in SECONDARY_SERVERS: 
            guild = self.bot.get_guild(config["guild_id"])
            # Проверка бота на сервере
            if not guild:
                results.append(f"Бот не на сервере {config['name']}")
                continue

            try:
                member_on_server = await guild.fetch_member(member.id)
                found_roles = []

                # Проверяем роли у участника на стороннем сервере
                for role_id in config["required_roles"]:
                    role = guild.get_role(role_id)
                    if role and role in member_on_server.roles:
                        found_roles.append(role.name)

                if found_roles:
                    has_any_valid_role = True
                    roles_str = ", ".join(found_roles)
                    results.append(f"Найдена роль {roles_str} на сервере {config['name']}")

                    # Выдача роли на основном сервере
                    role_to_give = member.guild.get_role(config["given_role_id"])
                    if role_to_give:
                        try:
                            await member.add_roles(role_to_give, reason=f"Участник сервера {config['name']}")
                            results.append(f"└ Выдана роль: {role_to_give.name}")
                        except disnake.Forbidden:
                            results.append(f"└ Ошибка выдачи роли")
                    else:
                        results.append(f"└ Роль для выдачи ({config['given_role_id']}) не найдена")
                else:
                    results.append(f"└ Нет нужной роли на сервере *{config['name']}*")

            except disnake.NotFound: 
                results.append(f"Пользователь не найден на *{config['name']}*")
            except disnake.HTTPException as e:
                results.append(f"Ошибка запроса к *{config['name']}*: {e}")

        # Кик пользователя в случае, если у него нет ролей на нужных серверах
        if not has_any_valid_role:
            try:
                await member.kick(reason="У пользователя нет ролей на серверах")
                results.append("\nПользователь был исключен с сервера.")
            except disnake.Forbidden:
                results.append("\nНе удалось исключить пользователя (недостаточно прав).")

        # Создание и отправка Embed-сообщения   
        embed_color = member.accent_color or disnake.Color.blue()
        embed_join = disnake.Embed(
            title='Новый пользователь на сервере', 
            color=embed_color, 
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed_join.set_thumbnail(url=member.display_avatar.url)
        embed_join.add_field(name='Пользователь', value=f'{member.mention}', inline=True)
        embed_join.add_field(name='ID', value=f'`{member.id}`', inline=True)
        embed_join.add_field(name='Логин', value=f'`{member.name}`', inline=True)
        
        results_text = "\n".join(results) if results else "Проверки не проводились"
        embed_join.add_field(name="Результаты проверок:", value=results_text, inline=False)
        
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed_join)
        else:
            print('Канал для отправки логов не найден!')

def setup(bot: commands.Bot):
    bot.add_cog(RoleChecker(bot))