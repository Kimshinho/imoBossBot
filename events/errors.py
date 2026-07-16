
from discord.ext.commands.errors import (
    CommandNotFound
)

from core.bot import bot

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, CommandNotFound):
        return

