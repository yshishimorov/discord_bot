import disnake
from disnake.ext import commands
import re

# ID ролей: leader, dep lead, high, tier check
ALLOWED_ROLE_IDS = [1117383882459840554, 1163952540719775774, 1117383882443075669, 1479207507883982979] 

# ID канала для отправки результатов
LOG_CHANNEL_ID = 1539394319088357427

ROLE_TIER_S = 1454182422315798821
ROLE_TIER_A = 1429873878175584328
ROLE_TIER_B = 1429846658841182339
ROLE_CAPT = 1454812955718848563

# Иерархия ролей (приоритет от 1 до 5)
ROLE_PRIORITY = {
    ROLE_TIER_S: (1, "🥇"),
    ROLE_TIER_A: (2, "🥈"),
    ROLE_TIER_B: (3, "🥉"),
    ROLE_CAPT: (4, "🔫"),
}

# Получаем роль пользователя и его приоритет в списке
def get_member_rank(member: disnake.Member):
    best_priority = 5  # Игрок без специальных ролей
    best_emoji = ""

    if member and hasattr(member, "roles"):
        for role in member.roles:
            if role.id in ROLE_PRIORITY:
                priority, emoji = ROLE_PRIORITY[role.id]
                if priority < best_priority:
                    best_priority = priority
                    best_emoji = emoji

    return best_priority, best_emoji


# Модальное окно для закрытия плюсов
class CloseCaptModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Результат матча (WIN / LOSE)",
                placeholder="Введите WIN или LOSE",
                custom_id="result_status",
                required=True,
                max_length=10
            )
        ]
        super().__init__(title="Закрытие плюсов и подведение итогов", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        result_input = inter.text_values["result_status"].strip().upper()

        if result_input not in ["WIN", "LOSE"]:
            return await inter.response.send_message("Пожалуйста, введите корректный результат: WIN или LOSE!", ephemeral=True)

        await inter.response.defer(ephemeral=True)

        embeds = inter.message.embeds
        info_embed = embeds[0]
        main_embed = embeds[1]
        res_embed = embeds[2]

        status_emoji = "🏆" if result_input == "WIN" else "❌"
        
        # Получаем данные из эмбедов для формирования текста
        vs_title = info_embed.title
        capt_time = info_embed.fields[0].value if len(info_embed.fields) > 0 else "Не указано"
        capt_group = info_embed.fields[1].value if len(info_embed.fields) > 1 else "Не указано"
        
        main_list = main_embed.fields[0].value
        res_list = res_embed.fields[0].value

        # Формируем обычный текстовый отчёт для логов
        log_text = (
            f"**{status_emoji} Итоги капта [{result_input}] — {vs_title}**\n"
            f"⏰ **Время:** {capt_time} | 🗝️ **Группа:** `{capt_group}`\n\n"
            f"👥 **{main_embed.fields[0].name}:**\n{main_list}\n\n"
            f"📋 **Резерв:**\n{res_list}"
        )

        # 1. Отправляем текстовый отчёт в канал логов
        log_channel = inter.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(content=log_text)

        # 2. Блокируем и архивируем ветку (если существует)
        if inter.message.thread:
            thread = inter.message.thread
            await thread.send(f"Плюсы закрыты! Исход матча: {result_input}")
            await thread.edit(locked=True, archived=True)

        # 3. Удаляем сообщение из основного канала
        await inter.message.delete()
        await inter.followup.send("Капт успешно закрыт, а итоги отправлены в логи текстом!", ephemeral=True)


# --- 2. Модальное окно для изменения данных капта ---
class EditInfoModal(disnake.ui.Modal):
    def __init__(self, main_embed: disnake.Embed):
        title_vs = main_embed.title.replace("CAPT VS ", "").strip()
        current_time = main_embed.fields[0].value if len(main_embed.fields) > 0 else ""
        current_group = main_embed.fields[1].value if len(main_embed.fields) > 1 else ""
        current_limit = main_embed.fields[2].value if len(main_embed.fields) > 2 else "35"

        components = [
            disnake.ui.TextInput(
                label="Против кого (VS)",
                placeholder="Например: Ballas",
                custom_id="new_vs",
                value=title_vs,
                required=True
            ),
            disnake.ui.TextInput(
                label="Новое время капта",
                placeholder="Например: 18:00",
                custom_id="new_time",
                value=current_time if current_time != "Не указано" else "",
                required=False
            ),
            disnake.ui.TextInput(
                label="Новый код группы",
                placeholder="5 символов",
                custom_id="new_group",
                value=current_group if current_group != "Не указано" else "",
                required=False,
                max_length=10
            ),
            disnake.ui.TextInput(
                label="Новый лимит участников",
                placeholder="Например: 35, 40, 50",
                custom_id="new_limit",
                value=current_limit,
                required=False
            )
        ]
        super().__init__(title="Изменение данных капта", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        new_vs = inter.text_values["new_vs"].strip()
        new_time = inter.text_values["new_time"].strip() or "Не указано"
        new_group = inter.text_values["new_group"].strip() or "Не указано"
        new_limit_str = inter.text_values["new_limit"].strip()

        try:
            new_limit = int(new_limit_str) if new_limit_str else 35
        except ValueError:
            return await inter.response.send_message("Лимит должен быть числом!", ephemeral=True)

        embeds = inter.message.embeds
        info_embed = embeds[0]
        main_embed = embeds[1]

        info_embed.title = f"CAPT VS {new_vs}"
        info_embed.set_field_at(0, name="Время", value=new_time, inline=True)
        info_embed.set_field_at(1, name="Группа", value=new_group, inline=True)
        info_embed.set_field_at(2, name="Лимит", value=str(new_limit), inline=True)

        current_count = 0
        if main_embed.fields[0].value != "Основной состав пуст":
            current_count = len(main_embed.fields[0].value.split("\n"))

        main_embed.set_field_at(0, name=f"Участники ({current_count}/{new_limit})", value=main_embed.fields[0].value, inline=True)

        await inter.response.edit_message(embeds=embeds)

        if inter.message.thread:
            new_thread_name = f"plus-capt-{new_time}"
            await inter.message.thread.edit(name=new_thread_name)


# --- 3. Выпадающее меню ---
class CaptSelect(disnake.ui.Select):
    def __init__(self):
        options = [
            disnake.SelectOption(
                label="Упомянуть основной список",
                emoji="⚠️",
                value="mention_main"
            ),
            disnake.SelectOption(
                label="Изменить данные",
                emoji="⚙️",
                value="edit_info"
            ),
            disnake.SelectOption(
                label="Закрыть плюсы (Результат)",
                emoji="🛑",
                value="close_capt"
            )
        ]
        super().__init__(
            placeholder="Выберите действие...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, inter: disnake.MessageInteraction):
        selected = self.values[0]

        has_role = any(role.id in ALLOWED_ROLE_IDS for role in inter.author.roles)
        is_admin = has_role or inter.author.guild_permissions.administrator

        if selected == "edit_info":
            if not is_admin:
                return await inter.response.send_message("У вас нет прав для изменения данных!", ephemeral=True)

            await inter.response.send_modal(EditInfoModal(inter.message.embeds[0]))

        elif selected == "close_capt":
            if not is_admin:
                return await inter.response.send_message("У вас нет прав для закрытия плюсов!", ephemeral=True)

            await inter.response.send_modal(CloseCaptModal())

        elif selected == "mention_main":
            main_embed = inter.message.embeds[1]
            main_field = main_embed.fields[0].value

            if main_field == "Основной состав пуст":
                return await inter.response.send_message("Основной состав пока пуст!", ephemeral=True)

            # Находим все теги пользователей через регулярное выражение
            mentions = re.findall(r"<@!?\d+>", main_field)

            if mentions:
                await inter.response.send_message(" ".join(mentions))
            else:
                await inter.response.send_message("Основной состав пока пуст!", ephemeral=True)


class CaptView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CaptSelect())


# --- 4. Основной Cog ---
class CaptchaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="capt",
        description="Открыть набор на капт"
    )
    async def capt(
        self,
        inter: disnake.ApplicationCommandInteraction,
        vs: str = commands.Param(description="Название команды-соперника (например: Ballas)"),
        time: str = commands.Param(default=None, description="Время капта"),
        group: str = commands.Param(default=None, description="Код группы (5 символов)"),
        limit: int = commands.Param(default=35, description="Ограничение основного состава (по умолчанию 35)")
    ):
        time_text = time if time else "Не указано"
        group_text = group if group else "Не указано"

        embed_info = disnake.Embed(title=f"CAPT VS {vs}", color=disnake.Color.red())
        embed_info.add_field(name="Время", value=time_text, inline=True)
        embed_info.add_field(name="Группа", value=group_text, inline=True)
        embed_info.add_field(name="Лимит", value=str(limit), inline=True)

        embed_main = disnake.Embed(title="Основной состав", color=disnake.Color.green())
        embed_main.add_field(name=f"Участники (0/{limit})", value="Основной состав пуст", inline=True)

        embed_reserve = disnake.Embed(title="Запасной состав", color=disnake.Color.orange())
        embed_reserve.add_field(name="Резерв", value="Список пуст", inline=True)

        await inter.response.send_message(
            embeds=[embed_info, embed_main, embed_reserve], 
            view=CaptView()
        )
        
        msg = await inter.original_message()

        thread_name = f"plus-capt-{time_text}"
        thread = await msg.create_thread(name=thread_name, auto_archive_duration=1440)

    # Обработка плюсов в ветке
    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return

        if isinstance(message.channel, disnake.Thread) and message.channel.name.startswith("plus-capt-"):
            if message.content.strip() == "+":
                thread = message.channel
                parent_msg = await thread.parent.fetch_message(thread.id)

                embeds = parent_msg.embeds
                main_embed = embeds[1]
                res_embed = embeds[2]
                
                user_mention = message.author.mention

                if user_mention in main_embed.fields[0].value or user_mention in res_embed.fields[0].value:
                    await message.add_reaction("❌")
                    return

                current_res_value = res_embed.fields[0].value
                if current_res_value == "Список пуст":
                    new_value = f"1. {user_mention}"
                else:
                    count = len(current_res_value.split("\n")) + 1
                    new_value = f"{current_res_value}\n{count}. {user_mention}"

                res_embed.set_field_at(0, name="Резерв", value=new_value, inline=True)
                await parent_msg.edit(embeds=embeds)
                await message.add_reaction("✅")

    # --- Добавление реакции ✅ ---
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: disnake.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id or str(payload.emoji) != "✅":
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if not member or not any(r.id in ALLOWED_ROLE_IDS for r in member.roles):
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, disnake.Thread) or not channel.name.startswith("plus-capt-"):
            return

        message = await channel.fetch_message(payload.message_id)
        if message.content.strip() != "+":
            return

        target_member = message.author
        user_mention = target_member.mention
        parent_msg = await channel.parent.fetch_message(channel.id)
        embeds = parent_msg.embeds

        info_embed = embeds[0]
        main_embed = embeds[1]
        res_embed = embeds[2]

        limit = int(info_embed.fields[2].value)

        # 1. Удаляем из резерва
        res_lines = [line for line in res_embed.fields[0].value.split("\n") if user_mention not in line]
        new_res_value = []
        for idx, line in enumerate(res_lines, 1):
            parts = line.split(". ")
            if len(parts) > 1:
                new_res_value.append(f"{idx}. {parts[1]}")
        
        res_embed.set_field_at(0, name="Резерв", value="\n".join(new_res_value) if new_res_value else "Список пуст", inline=True)

        # 2. Перестраиваем Основной состав
        current_members = []

        if main_embed.fields[0].value != "Основной состав пуст":
            for line in main_embed.fields[0].value.split("\n"):
                if "<@" in line:
                    user_id_str = line.split("<@")[1].split(">")[0].replace("!", "")
                    m = guild.get_member(int(user_id_str))
                    if m and m not in current_members:
                        current_members.append(m)

        if target_member not in current_members:
            current_members.append(target_member)

        if len(current_members) > limit:
            current_members.pop()
            return await message.add_reaction("⚠️")

        sorted_members = sorted(current_members, key=lambda m: get_member_rank(m)[0])

        new_main_lines = []
        for idx, m in enumerate(sorted_members, 1):
            _, emoji = get_member_rank(m)
            emoji_prefix = f" {emoji}" if emoji else ""
            new_main_lines.append(f"{idx}.{emoji_prefix} {m.mention}")

        main_embed.set_field_at(
            0, 
            name=f"Участники ({len(sorted_members)}/{limit})", 
            value="\n".join(new_main_lines) if new_main_lines else "Основной состав пуст", 
            inline=True
        )

        await parent_msg.edit(embeds=embeds)

    # --- Снятие реакции ✅ ---
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: disnake.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id or str(payload.emoji) != "✅":
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, disnake.Thread) or not channel.name.startswith("plus-capt-"):
            return

        message = await channel.fetch_message(payload.message_id)
        target_member = message.author
        user_mention = target_member.mention
        
        parent_msg = await channel.parent.fetch_message(channel.id)
        embeds = parent_msg.embeds

        info_embed = embeds[0]
        main_embed = embeds[1]
        res_embed = embeds[2]

        limit = int(info_embed.fields[2].value)

        current_members = []
        if main_embed.fields[0].value != "Основной состав пуст":
            for line in main_embed.fields[0].value.split("\n"):
                if "<@" in line:
                    user_id_str = line.split("<@")[1].split(">")[0].replace("!", "")
                    m = guild.get_member(int(user_id_str))
                    if m and m.id != target_member.id:
                        current_members.append(m)

        sorted_members = sorted(current_members, key=lambda m: get_member_rank(m)[0])

        new_main_lines = []
        for idx, m in enumerate(sorted_members, 1):
            _, emoji = get_member_rank(m)
            emoji_prefix = f" {emoji}" if emoji else ""
            new_main_lines.append(f"{idx}.{emoji_prefix} {m.mention}")

        main_embed.set_field_at(
            0, 
            name=f"Участники ({len(sorted_members)}/{limit})", 
            value="\n".join(new_main_lines) if new_main_lines else "Основной состав пуст", 
            inline=True
        )

        res_val = res_embed.fields[0].value
        if user_mention not in res_val:
            if res_val == "Список пуст":
                new_res = f"1. {user_mention}"
            else:
                lines = res_val.split("\n")
                new_res = f"{res_val}\n{len(lines) + 1}. {user_mention}"

            res_embed.set_field_at(0, name="Резерв", value=new_res, inline=True)

        await parent_msg.edit(embeds=embeds)


def setup(bot: commands.Bot):
    bot.add_cog(CaptchaCog(bot))