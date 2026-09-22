import datetime

from discord.ext import tasks

from core.boss_data import BOSS_DATA
from core import storage

from utils.sender import send_to_target_channel

@tasks.loop(seconds=1)
async def boss_check_loop():

    now = datetime.datetime.now()

    # ============================
    # 금서고 특정 시간 알림 처리 (HH:MM:SS 기준 유동 변경 가능)
    # ============================
    # 💡 아래 리스트에 원하는 정각 알림 시각을 자유롭게 추가/수정하여 테스트할 수 있습니다.
    target_times = ["11:00:00", "23:00:00"]

    if not hasattr(storage, 'system_notified_records'):

        storage.system_notified_records = {}

    for t_str in target_times:

        # 각 목표 시간 오브젝트 계산
        t_h, t_m, t_s = map(int, t_str.split(':'))

        target_datetime = now.replace(
            hour=t_h,
            minute=t_m,
            second=t_s,
            microsecond=0
        )

        day_key = target_datetime.strftime('%Y-%m-%d-%H-%M')

        if day_key not in storage.system_notified_records:

            storage.system_notified_records[day_key] = []

        # 현재 시간과 목표 시간과의 초 단위 차이 계산
        diff_seconds = int((target_datetime - now).total_seconds())

        if diff_seconds == 600 and 10 not in storage.system_notified_records[day_key]:

            await send_to_target_channel(
                "📢 @everyone 금서고 10분 전입니다."
            )

            storage.system_notified_records[day_key].append(10)

        elif diff_seconds == 300 and 5 not in storage.system_notified_records[day_key]:

            await send_to_target_channel(
                "⚠️ @everyone 금서고 5분 전입니다."
            )

            storage.system_notified_records[day_key].append(5)

        elif diff_seconds == 60 and 1 not in storage.system_notified_records[day_key]:

            await send_to_target_channel(
                "🔥 @everyone 금서고 1분 전입니다."
            )

            storage.system_notified_records[day_key].append(1)

        elif diff_seconds == 0 and 0 not in storage.system_notified_records[day_key]:

            await send_to_target_channel(
                "⚔️ @everyone 금서고 타임입니다."
            )

            storage.system_notified_records[day_key].append(0)

    for boss, gen_time in list(storage.boss_timers.items()):

        # ============================
        # 미입력 3회 이상 자동 삭제 체크
        # ============================
        extend_count = storage.extend_counts.get(
            boss,
            0
        )

        if extend_count >= 3:
            
            storage.boss_timers.pop(
                boss,
                None
            )
            
            if boss in storage.notified_records:
                del storage.notified_records[boss]
            
            storage.extend_counts[boss] = 0
            
            await send_to_target_channel(
                f"💀 {boss} 미입력 {extend_count}회\n"
                f"🔴 자동 삭제됨"
            )
            
            continue

        # 유동적 젠 타임 데이터 기반 리스트 언패킹 처리
        boss_info = BOSS_DATA.get(boss)

        if not boss_info:
            continue

        # 현재 보스의 회차 정보를 기반으로 현재 타임 문자열 획득
        current_cut_count = storage.cut_counts.get(boss, 1)

        time_list = [t.strip() for t in boss_info['time'].split(',')]

        if current_cut_count <= len(time_list):

            boss_time_str = time_list[current_cut_count - 1]

        else:

            boss_time_str = time_list[-1]

        h, m, s = map(
            int,
            boss_time_str.split(':')
        )

        remaining_seconds = int(
            (gen_time - now).total_seconds()
        )

        if boss not in storage.notified_records:
            storage.notified_records[boss] = []

        if remaining_seconds == 600 and 10 not in storage.notified_records[boss]:

            await send_to_target_channel(
                f"📢 @everyone {boss} 10분 전입니다."
            )

            storage.notified_records[boss].append(10)

        elif remaining_seconds == 300 and 5 not in storage.notified_records[boss]:

            await send_to_target_channel(
                f"⚠️ @everyone {boss} 5분 전입니다."
            )

            storage.notified_records[boss].append(5)

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

            storage.extend_counts[boss] = min(
                storage.extend_counts.get(boss, 0) + 1,
                3
            )

            next_time = gen_time + datetime.timedelta(
                hours=h,
                minutes=m,
                seconds=s
            )

            storage.boss_timers[boss] = next_time
            storage.notified_records[boss] = []

           # await send_to_target_channel(
           #    f"🔄 {boss} 자동 연장 완료\n"
           #    f"➡️ 다음 젠: {next_time.strftime('%H:%M:%S')}"
           # )
