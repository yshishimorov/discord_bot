import os
import disnake
from disnake.ext import commands
import config

intents = disnake.Intents.all()

bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен!")

@bot.command()
@commands.is_owner() # Только для владельца бота
async def reload(ctx, extension: str):
    try:
        bot.reload_extension(f"cogs.{extension}")
        await ctx.send(f"Модуль `{extension}` успешно перезагружен! ✅")
    except Exception as e:
        await ctx.send(f"Ошибка при перезагрузке: `{e}` ❌")

# Автоматическая загрузка всех когов из папки cogs
for filename in os.listdir("./cogs"):
    # Проверяем, что это .py файл и он не начинается с подчеркивания (например, __init__.py)
    if filename.endswith(".py") and not filename.startswith("__"):
        bot.load_extension(f"cogs.{filename[:-3]}")
        print(f"Загружен модуль: {filename[:-3]}")

if __name__ == "__main__":
    bot.run(config.TOKEN)