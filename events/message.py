
import discord
import datetime
import re
import json
import os

from core.bot import bot
from core.boss_data import BOSS_DATA
from core import storage

from views.move_confirm import MoveConfirmView

def save_custom_boss(boss_name, time_str, boss_alias):
    """커스텀 보스를 파일에 저장"""
    try:
        custom_boss_file = os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "custom_bosses.json"
        )
        
        # 기존 커스텀 보스 로드
        if os.path.exists(custom_boss_file):
            with open(custom_boss_file, 'r', encoding='utf-8') as f:
                custom = json.load(f)
        else:
            custom = {}
        
        # 새 보스 추가
        custom[boss_name] = {"time": time_str, "alias": boss_alias}
        BOSS_DATA[boss_name] = {"time": time_str, "alias": boss_alias}
        
        # 파일 저장
        os.makedirs(os.path.dirname(custom_boss_file), exist_ok=True)
        with open(custom_boss_file, 'w', encoding='utf-8') as f:
            json.dump(custom, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"❌ 보스 저장 실패: {e}")
        return False

def delete_custom_boss(boss_name):
    """보스목록에서 커스텀 보스 삭제"""
    try:
        custom_boss_file = os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "custom_bosses.json"
        )
        
        # 기존 커스텀 보스 로드
        if os.path.exists(custom_boss_file):
            with open(custom_boss_file, 'r', encoding='utf-8') as f:
                custom = json.load(f)
        else:
            custom = {}
        
        # 보스 삭제
        if boss_name in custom:
            del custom[boss_name]
            
            # BOSS_DATA에서도 제거
            if boss_name in BOSS_DATA:
                del BOSS_DATA[boss_name]
            
            # 파일 저장
            with open(custom_boss_file, 'w', encoding='utf-8') as f:
                json.dump(custom, f, ensure_ascii=False, indent=2)
            
            return True
        
        return False
    except Exception as e:
        print(f"❌ 보스 삭제 실패: {e}")
        return False

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
    if content in ["메뉴얼", "명령어"]:

        manual = (
            "🎮 아이모 보스탐 매니저 v1.2\n\n"

            "═══════════════════════════════════\n"
            "📋 [보스 관리]\n"
            "═══════════════════════════════════\n\n"

            "📋 보스목록 조회\n"
            "`보스목록`\n"
            "• 전체 등록 보스 및 젠 타임 확인\n\n"

            "➕ 보스 등록\n"
            "`보스등록 02:30:00 여왕(ㅇㅇ)`\n"
            "• 형식: 시간(HH:MM:SS) 보스명(약어)\n"
            "• 커스텀 보스 추가 가능\n"
            "• 재시작 후에도 유지\n\n"

            "🗑️ 보스목록 삭제\n"
            "`보스삭제 깬`\n"
            "• 보스를 목록에서 완전 삭제\n"
            "• 기본 보스는 자동 보호\n\n"

            "═══════════════════════════════════\n"
            "⚔️ [보스 타이밍 관리]\n"
            "═══════════════════════════════════\n\n"

            "⚔️ 보스 컷 기록\n"
            "`와당컷` 또는 `ㅇㄷㅋ`\n"
            "• 현재 시각 기준으로 젠 타임 계산\n"
            "• 미입력 카운트 자동 관리\n\n"

            "⏱️ 과거 시간 기준 컷\n"
            "`1304 깬컷` 또는 `깬컷 13:04`\n"
            "• 23시 15분 기준으로 컷 기록\n"
            "• 정확한 젠 타임 계산 가능\n\n"

            "❌ 현황에서 삭제\n"
            "`깬삭제`\n"
            "• 보스를 현황에서만 제거\n"
            "• 다시 컷 입력 가능\n\n"

            "🔴 자동 삭제 (미입력 3회) ⭐ NEW\n"
            "• 미입력이 자동으로 인식됩니다\n"
            "• 미입력 3회시 보스현황에서 자동삭제\n"
            "• 별도 명령어 불필요\n\n"

            "═══════════════════════════════════\n"
            "📊 [현황 조회]\n"
            "═══════════════════════════════════\n\n"

            "📊 현재 보스 현황\n"
            "`보스탐` 또는 `현황`\n"
            "• 등록된 보스별 젠 시간\n"
            "• 미입력 횟수 표시\n"
            "• 미예약 보스 목록\n\n"

            "═══════════════════════════════════"
        )

        await message.channel.send(manual)
        return

    # =====================
    # 보스 등록
    # =====================
    if content.startswith("보스등록"):

        parts = content.replace("보스등록", "").strip().split()

        if len(parts) < 2:

            await message.channel.send(
                "❌ 형식 오류\n"
                "예시: `보스등록 02:30:00 여왕(ㅇㅇ)`"
            )

            return

        time_str = parts[0]

        boss_info_str = " ".join(parts[1:])

        # 시간 형식 검증
        if not re.match(r'^\d{1,2}:\d{2}:\d{2}$', time_str):

            await message.channel.send(
                "❌ 시간 형식 오류\n"
                "예시: 02:30:00 (HH:MM:SS)"
            )

            return

        # 보스이름(약어) 파싱
        match = re.match(r'(.+?)\((.+?)\)', boss_info_str)

        if not match:

            await message.channel.send(
                "❌ 보스 정보 형식 오류\n"
                "예시: `보스등록 02:30:00 여왕(ㅇㅇ)`"
            )

            return

        boss_name = match.group(1).strip()

        boss_alias = match.group(2).strip()

        # 중복 확인
        if boss_name in BOSS_DATA:

            await message.channel.send(
                f"⚠️ '{boss_name}'은(는) 이미 등록된 보스입니다."
            )

            return

        # 약어 중복 확인
        for name, info in BOSS_DATA.items():

            if info['alias'] == boss_alias:

                await message.channel.send(
                    f"⚠️ 약어 '{boss_alias}'은(는) "
                    f"'{name}'에서 이미 사용 중입니다."
                )

                return

        # 보스 저장
        if save_custom_boss(boss_name, time_str, boss_alias):

            await message.channel.send(
                f"✅ 보스 등록 완료!\n"
                f"👹 {boss_name}({boss_alias})\n"
                f"⏱️ 젠 타임: {time_str}"
            )

        else:

            await message.channel.send(
                "❌ 보스 저장 실패"
            )

        return

    # =====================
    # 보스 목록 삭제
    # =====================
    if content.startswith("보스삭제"):

        input_name = content.replace("보스삭제", "").strip()

        if not input_name:

            await message.channel.send(
                "❌ 형식 오류\n"
                "예시: `보스삭제 깬`"
            )

            return

        # 보스 찾기
        target_boss = None

        for name, info in BOSS_DATA.items():

            if (
                name == input_name
                or info['alias'] == input_name
            ):
                target_boss = name
                break

        if not target_boss:

            await message.channel.send(
                f"⚠️ '{input_name}' 보스를 찾을 수 없습니다."
            )

            return

        # 보스 삭제
        if delete_custom_boss(target_boss):

            await message.channel.send(
                f"✅ '{target_boss}' 보스목록 삭제 완료!"
            )

        else:

            await message.channel.send(
                f"⚠️ '{target_boss}'은(는) 기본 보스라 삭제할 수 없습니다."
            )

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
            r'^\d{2,4}$|^\d{1,2}:\d{2}$',
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

            # =================
            # 미입력 3회 이상 자동 삭제
            # =================
            extend_count = storage.extend_counts.get(
                target_boss,
                0
            )

            if extend_count >= 3:

                del storage.boss_timers[
                    target_boss
                ]

                if target_boss in storage.notified_records:
                    del storage.notified_records[
                        target_boss
                    ]

                storage.extend_counts[
                    target_boss
                ] = 0

                await message.channel.send(
                    f"💀 {target_boss} 컷 확인!\n"
                    f"{cut_msg}"
                    f"⚠️ 미입력 {extend_count}회\n"
                    f"🔴 현황에서 자동 삭제됨"
                )

                return

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
