import discord
from discord.ext import commands

from core.config import TOKEN

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix='',
    intents=intents
)

def run_bot():

    if TOKEN is None:
        print("❌ DISCORD_TOKEN 없음")
        return

    bot.run(TOKEN)
