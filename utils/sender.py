
from core.bot import bot
from core import storage

async def send_to_target_channel(message_text):

    if storage.target_channel_id is None:
        return

    channel = bot.get_channel(
        storage.target_channel_id
    )

    if channel:

        permissions = channel.permissions_for(
            channel.guild.me
        )

        if permissions.send_messages:
            await channel.send(message_text)

