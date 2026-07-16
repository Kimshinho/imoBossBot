import datetime

from discord.ext import tasks

from core.boss_data import BOSS_DATA
from core import storage

from utils.sender import send_to_target_channel

@tasks.loop(seconds=1)
async def boss_check_loop():

    now = datetime.datetime.now()

    for boss, gen_time in list(storage.boss_timers.items()):

        # ============================
        # 미입력 3회 이상 자동 삭제 체크
        # ============================
        extend_count = storage.extend_counts.get(
            boss,
            0
        )

        if extend_count >= 3:
            
            del storage.boss_timers[boss]
            
            if boss in storage.notified_records:
                del storage.notified_records[boss]
            
            storage.extend_counts[boss] = 0
            
            await send_to_target_channel(
                f"💀 {boss} 미입력 {extend_count}회\n"
                f"🔴 자동 삭제됨"
            )
            
            continue

        h, m, s = map(
            int,
            BOSS_DATA[boss]['time'].split(':')
        )

        remaining_seconds = int(
            (gen_time - now).total_seconds()
        )

        if boss not in storage.notified_records:
            storage.notified_records[boss] = []

        if remaining_seconds == 300 and 5 not in storage.notified_records[boss]:

            await send_to_target_channel(
                f"📢 @everyone {boss} 5분 전입니다."
            )

            storage.notified_records[boss].append(5)

        elif remaining_seconds == 180 and 3 not in storage.notified_records[boss]:

            await send_to_target_channel(
                f"⚠️ @everyone {boss} 3분 전입니다."
            )

            storage.notified_records[boss].append(3)

        elif remaining_seconds == 60 and 1 not in storage.notified_records[boss]:

            await send_to_target_channel(
                f"🔥 @everyone {boss} 1분 전입니다."
            )

            storage.notified_records[boss].append(1)

        elif remaining_seconds == 0 and 0 not in storage.notified_records[boss]:

            await send_to_target_channel(
                f"⚔️ @everyone {boss} 타임입니다."
            )

            storage.notified_records[boss].append(0)

        elif remaining_seconds <= -10:

            storage.extend_counts[boss] = (
                storage.extend_counts.get(boss, 0) + 1
            )

            next_time = gen_time + datetime.timedelta(
                hours=h,
                minutes=m,
                seconds=s
            )

            storage.boss_timers[boss] = next_time
            storage.notified_records[boss] = []

            await send_to_target_channel(
                f"🔄 {boss} 자동 연장 완료\n"
                f"➡️ 다음 젠: {next_time.strftime('%H:%M:%S')}"
            )
