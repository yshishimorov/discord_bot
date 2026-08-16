import disnake
from disnake.ext import commands
import datetime

PRIMARY_SERVER_ID = 1536873302142877746
LOG_CHANNEL_ID = 1538659863448657972 

class MemberLeaveLogger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        if member.guild.id != PRIMARY_SERVER_ID:
            return

        guild = member.guild
        reason_text = ""

        # Проверяем записи аудита за последние 10 секунд
        now = datetime.datetime.now(datetime.timezone.utc)
        
        async for entry in guild.audit_logs(limit=5):
            # Проверяем, была ли запись сделана недавно (в пределах 10 секунд)
            if (now - entry.created_at).total_seconds() < 10:
                if entry.target and entry.target.id == member.id:
                    if entry.action == disnake.AuditLogAction.kick:
                        audit_reason = entry.reason or "Причина не указана"
                        reason_text = f"Кикнут модератором {entry.user.mention}\nПричина: {audit_reason}"
                        break
                    elif entry.action == disnake.AuditLogAction.ban:
                        audit_reason = entry.reason or "Причина не указана"
                        reason_text = f"Забанен модератором {entry.user.mention}\nПричина: {audit_reason}"
                        break

        # Создание и отправка Embed-сообщения
        embed = disnake.Embed(
            title='Пользователь покинул сервер', 
            color=member.accent_color, 
            timestamp=now
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name='Пользователь', value=member.mention, inline=True)
        embed.add_field(name='ID', value=str(member.id), inline=True)
        embed.add_field(name='Логин', value=member.name, inline=True)
        
        if reason_text:
            embed.add_field(name='Причина ухода', value=reason_text, inline=False)
        else:
            embed.add_field(name='Статус', value="Вышел самостоятельно", inline=False)

        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
        else:
            print('Канал для отправки логов не найден!')

def setup(bot: commands.Bot):
    bot.add_cog(MemberLeaveLogger(bot))