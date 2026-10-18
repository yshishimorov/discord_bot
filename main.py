import os
import config
import disnake
from disnake.ext import commands

intents = disnake.Intents.all()

bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)

@bot.event
async def on_ready():
    print("Бот успешно запущен.")

@bot.command()
@commands.is_owner()

async def r(ctx, extension: str):
    await ctx.message.delete()
    try:
        bot.reload_extension(f"cogs.{extension}")
        await ctx.send(f"Модуль `{extension}` успешно перезагружен! ✅")
    except Exception as e:
        await ctx.send(f"Ошибка при перезагрузке: `{e}`")

# Автоматическая загрузка всех когов из папки cogs
for filename in os.listdir("./cogs"):
    # Проверяем, что это .py файл и он не начинается с подчеркивания
    if filename.endswith(".py") and not filename.startswith("__"):
        bot.load_extension(f"cogs.{filename[:-3]}")
        print(f"Загружен модуль: {filename[:-3]}")

if __name__ == "__main__":
    bot.run(config.TOKEN)