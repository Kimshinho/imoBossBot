
async def send_to_target_channel(channel, text):

    if channel:
        await channel.send(text)
