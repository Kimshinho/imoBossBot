
import discord
import datetime
import re

from core.bot import bot
from core.boss_data import BOSS_DATA
from core import storage

from views.move_confirm import MoveConfirmView

@bot.event
async def on_message(message):

    if message.author == bot.user:
        return

    content = message.content.strip()

    

    # =====================
    # 봇 소환
    # =====================
    if content == f"!{bot.user.name}":

        if storage.target_channel_id is None:

            storage.target_channel_id = (
                message.channel.id
            )

            await message.channel.send(
                f"⚙️ {bot.user.name} 최초 소환 완료!\n"
                f"현재 채널: #{message.channel.name}"
            )

        else:

            if (
                message.channel.id
                == storage.target_channel_id
            ):

                await message.channel.send(
                    "ℹ️ 현재 채널에서 이미 사용 중입니다."
                )

            else:

                view = MoveConfirmView(
                    message.channel.id
                )

                await message.channel.send(
                    "⚠️ 다른 채널에서 사용 중입니다.\n"
                    "이 채널로 이동하시겠습니까?",
                    view=view
                )

        return

    # =====================
    # 활성 채널 미설정
    # =====================
    if storage.target_channel_id is None:

        if (
            content in [
                "보스목록",
                "보스",
                "보스탐",
                "현황",
                "메뉴얼"
            ]
            or "컷" in content
            or "삭제" in content
            or content.endswith("ㅋ")
        ):

            await message.channel.send(
                f"⚠️ 먼저 사용할 채널에서 "
                f"`!{bot.user.name}` 입력"
            )

        return

    # =====================
    # 다른 채널 무시
    # =====================
    if (
        message.channel.id
        != storage.target_channel_id
    ):
        return

    # =====================
    # 보스 목록
    # =====================
    if content in ["보스목록", "보스"]:

        msg = (
            "📋 [아이모 기본 등록 보스 목록]\n"
            "현재 바로 사용 가능한 보스 리스트입니다.\n\n"
        )

        for name, info in BOSS_DATA.items():

            h, m, s = info['time'].split(':')

            formatted_time = (
                f"{int(h):03d}:{m}:{s}"
            )

            msg += (
                f"⏱️ 젠 타임 : "
                f"[{formatted_time}]  -  "
                f"👹 {name}({info['alias']})\n"
            )

        msg += (
            "\n"
            "👉 명령어로 사용할 때는 "
            "약어컷, 보스명컷 또는 "
            "초성으로 약어ㅋ를 입력해 주세요."
        )

        await message.channel.send(msg)
        return

    # =====================
    # 현황
    # =====================
    if content in ["보스탐", "현황", "보스"]:

        msg = "📋 [현재 보스 현황]\n```"

        if storage.boss_timers:

            sorted_bosses = sorted(
                storage.boss_timers.items(),
                key=lambda x: x[1]
            )

            for boss, gen_time in sorted_bosses:

                count = storage.extend_counts.get(
                    boss,
                    0
                )

                count_text = (
                    f" (미입력 {count}회)"
                    if count > 0
                    else ""
                )

                msg += (
                    f"\n{gen_time.strftime('%H:%M:%S')} "
                    f"{boss}{count_text}"
                )

        else:
            msg += "\n현재 등록된 보스 없음"

        msg += "\n```"

        unregistered = [
            boss
            for boss in BOSS_DATA.keys()
            if boss not in storage.boss_timers
        ]

        msg += "\n📋 [미예약 보스]\n```"

        if unregistered:
            msg += "\n" + ", ".join(unregistered)
        else:
            msg += "\n없음"

        msg += "\n```"

        await message.channel.send(msg)
        return

    # =====================
    # 메뉴얼
    # =====================
    if content == "메뉴얼":

        manual = (
            "🎮 아이모 보스탐 매니저\n\n"

            "📋 보스목록\n"
            "`보스목록`\n\n"

            "⚔️ 컷 입력\n"
            "`와당컷`\n"
            "`ㅇㄷㅋ`\n\n"

            "⏱️ 과거 시간 입력\n"
            "`1304 깬컷`\n"
            "`깬컷 13:04`\n\n"

            "❌ 삭제\n"
            "`깬삭제`\n\n"

            "📊 현황\n"
            "`보스탐`"
        )

        await message.channel.send(manual)
        return

    # =====================
    # 삭제 처리
    # =====================
    if "삭제" in content:

        input_name = content.replace(
            "삭제",
            ""
        ).strip()

        target_boss = None

        for name, info in BOSS_DATA.items():

            if (
                name == input_name
                or info['alias'] == input_name
            ):
                target_boss = name
                break

        if target_boss:

            if target_boss in storage.boss_timers:
                del storage.boss_timers[target_boss]

            if (
                target_boss
                in storage.notified_records
            ):
                del storage.notified_records[
                    target_boss
                ]

            storage.extend_counts[target_boss] = 0

            await message.channel.send(
                f"❌ {target_boss} 삭제 완료"
            )

        return

    # =====================
    # 컷 처리
    # =====================
    words = content.split()

    cmd_part = ""
    time_part = ""

    for word in words:

        if "컷" in word or (
            word.endswith("ㅋ")
            and len(word) > 1
        ):
            cmd_part = word

        elif re.match(
            r'^\\d{1,2}:?\\d{2}$',
            word
        ):
            time_part = word.replace(":", "")

    if cmd_part:

        input_name = ""

        if "컷" in cmd_part:
            input_name = (
                cmd_part.replace("컷", "")
                .strip()
            )

        elif cmd_part.endswith("ㅋ"):
            input_name = (
                cmd_part[:-1].strip()
            )

        target_boss = None
        boss_info = None

        for name, info in BOSS_DATA.items():

            if (
                name == input_name
                or info['alias'] == input_name
            ):
                target_boss = name
                boss_info = info
                break

        if target_boss:

            if (
                target_boss
                in storage.boss_timers
            ):
                del storage.boss_timers[
                    target_boss
                ]

            storage.notified_records[
                target_boss
            ] = []

            storage.extend_counts[
                target_boss
            ] = 0

            target_h, target_m, target_s = map(
                int,
                boss_info['time'].split(':')
            )

            now = datetime.datetime.now()

            # =================
            # 과거 시간 입력
            # =================
            if time_part:

                try:

                    if len(time_part) == 4:

                        cut_h = int(
                            time_part[:2]
                        )

                        cut_m = int(
                            time_part[2:]
                        )

                    else:

                        cut_h = int(
                            time_part[:1]
                        )

                        cut_m = int(
                            time_part[1:]
                        )

                    base_time = now.replace(
                        hour=cut_h,
                        minute=cut_m,
                        second=0,
                        microsecond=0
                    )

                    if base_time > now:
                        base_time -= (
                            datetime.timedelta(
                                days=1
                            )
                        )

                    cut_msg = (
                        f"⏱️ {cut_h:02d}:"
                        f"{cut_m:02d} 기준 계산\n"
                    )

                except Exception:

                    await message.channel.send(
                        "❌ 시간 형식 오류\n"
                        "예시: 1304 또는 13:04"
                    )

                    return

            else:

                base_time = now

                cut_msg = (
                    "⚡ 실시간 컷 기록\n"
                )

            # =================
            # 다음 젠 계산
            # =================
            next_gen_time = (
                base_time
                + datetime.timedelta(
                    hours=target_h,
                    minutes=target_m,
                    seconds=target_s
                )
            )

            is_extended = False

            while next_gen_time < now:

                next_gen_time += (
                    datetime.timedelta(
                        hours=target_h,
                        minutes=target_m,
                        seconds=target_s
                    )
                )

                storage.extend_counts[
                    target_boss
                ] = (
                    storage.extend_counts.get(
                        target_boss,
                        0
                    ) + 1
                )

                is_extended = True

            if is_extended:

                cut_msg += (
                    "🔄 미래 시간으로 "
                    "자동 연장 완료\n"
                )

            storage.boss_timers[
                target_boss
            ] = next_gen_time

            await message.channel.send(
                f"💀 {target_boss} 컷 확인!\n"
                f"{cut_msg}"
                f"⏰ 다음 젠 시간\n"
                f"{next_gen_time.strftime('%H시 %M분 %S초')}"
            )

            return

    await bot.process_commands(message)
