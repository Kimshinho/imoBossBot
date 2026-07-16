from core.bot import bot
from tasks.boss_loop import boss_check_loop

@bot.event
async def on_ready():

    print(
        f"[{bot.user.name}] "
        f"아이모 보스탐 매니저 가동 완료!"
    )

    if not boss_check_loop.is_running():
        boss_check_loop.start()
