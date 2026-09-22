import discord
import datetime
import re
import json
import os

from core.bot import bot
from core.boss_data import BOSS_DATA
from core import storage

from views.move_confirm import MoveConfirmView
from utils.time_utils import now as current_time


def parse_cut_time(value):
    """컷 명령어의 입력 시간을 시, 분, 초로 변환한다."""
    if ":" in value:
        parts = value.split(":")
        if len(parts) not in (2, 3):
            return None
        if not all(part.isdigit() for part in parts):
            return None
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) == 3 else 0
    elif value.isdigit() and len(value) in (3, 4):
        hour = int(value[:-2])
        minute = int(value[-2:])
        second = 0
    else:
        return None

    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        return None

    return hour, minute, second


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
            or "초기화" in content
            or "전체삭제" in content
            or "젠" in content
                              
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
            r'^\d{3,4}$|^\d{1,2}:\d{2}(?::\d{2})?$',
            word
        ):
            time_part = word

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

            # 컷 카운트 반영 공간 초기화 검증
            if not hasattr(storage, 'cut_counts'):

                storage.cut_counts = {}

            # 유동적 젠 타임 데이터 기반 자동 분기 처리
            current_cut_count = storage.cut_counts.get(target_boss, 0) + 1

            storage.cut_counts[target_boss] = current_cut_count

            # 콤마 단위로 등록된 시간들을 리스트로 추출
            time_list = [t.strip() for t in boss_info['time'].split(',')]

            # 현재 회차가 등록된 시간 개수 내라면 매칭되는 시간을 사용, 넘어섰다면 마지막 시간을 고정 사용
            if current_cut_count <= len(time_list):

                boss_time_str = time_list[current_cut_count - 1]

            else:

                boss_time_str = time_list[-1]

            target_h, target_m, target_s = map(
                int,
                boss_time_str.split(':')
            )

            now = current_time()

            # =================
            # 과거 시간 입력
            # =================
            if time_part:

                try:
                    parsed_time = parse_cut_time(time_part)

                    if parsed_time is None:
                        raise ValueError("invalid cut time")

                    cut_h, cut_m, cut_s = parsed_time

                    base_time = now.replace(
                        hour=cut_h,
                        minute=cut_m,
                        second=cut_s,
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
                        f"{cut_m:02d}:{cut_s:02d} 기준 계산\n"
                    )

                except Exception:

                    await message.channel.send(
                        "❌ 시간 형식 오류\n"
                        "예시: 1304, 13:04 또는 13:04:30"
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

                # 과거 시각을 직접 입력한 경우는 누락 알림이 아니라
                # 다음 미래 젠을 계산하는 입력이므로 미입력 횟수에 포함하지 않는다.
                if not time_part:
                    storage.extend_counts[
                        target_boss
                    ] = min(
                        storage.extend_counts.get(
                            target_boss,
                            0
                        ) + 1,
                        3
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

                storage.boss_timers.pop(
                    target_boss,
                    None
                )

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

    # =====================
    # 보스 확정 젠 타임 직접 지정 (예: 12:12:00 깬 젠)
    # =====================
    if content.endswith("젠"):

        registration_messages = []

        for zen_line in content.splitlines():

            zen_line = zen_line.strip()

            if not zen_line.endswith("젠"):
                continue

            zen_input = zen_line[:-1].strip()

            # 패턴 1: 시간(HH:MM:SS 또는 HH:MM) + 보스명
            match_zen_prefix = re.match(
                r'^(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$',
                zen_input
            )

            # 패턴 2: 보스명 + 시간(HH:MM:SS 또는 HH:MM)
            match_zen_suffix = re.match(
                r'^(.+?)\s+(\d{1,2}:\d{2}(?::\d{2})?)$',
                zen_input
            )

            if match_zen_prefix:
                zen_time_target = match_zen_prefix.group(1)
                boss_input_target = match_zen_prefix.group(2).strip()
            elif match_zen_suffix:
                boss_input_target = match_zen_suffix.group(1).strip()
                zen_time_target = match_zen_suffix.group(2)
            else:
                continue

            found_boss = None

            for name, info in BOSS_DATA.items():
                if name == boss_input_target or info['alias'] == boss_input_target:
                    found_boss = name
                    break

            if not found_boss:
                continue

            time_parts = zen_time_target.split(':')
            h = int(time_parts[0])
            m = int(time_parts[1])
            s = int(time_parts[2]) if len(time_parts) == 3 else 0

            if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
                continue

            now = current_time()
            target_gen_time = now.replace(
                hour=h,
                minute=m,
                second=s,
                microsecond=0
            )

            if target_gen_time < now:
                target_gen_time += datetime.timedelta(days=1)

            storage.boss_timers[found_boss] = target_gen_time
            storage.extend_counts[found_boss] = 0

            # 확정 젠 등록 후에는 유동 보스의 마지막 젠 타임을 계속 사용한다.
            if not hasattr(storage, 'cut_counts'):
                storage.cut_counts = {}

            time_list = [
                value.strip()
                for value in BOSS_DATA[found_boss]['time'].split(',')
            ]
            storage.cut_counts[found_boss] = len(time_list)

            if (
                hasattr(storage, 'notified_records')
                and found_boss in storage.notified_records
            ):
                storage.notified_records[found_boss] = []

            registration_messages.append(
                f"📅 **{found_boss}** 확정 젠 타임 등록!\n"
                f"• 다음 젠: **{target_gen_time.strftime('%H:%M:%S')}**"
            )

        if registration_messages:
            await message.channel.send("\n\n".join(registration_messages))
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

            # 콤마로 구분된 유동 시간 목록 중 첫 번째(1회차) 시간만 안전하게 split
            first_time_str = info['time'].split(',')[0].strip()

            h, m, s = first_time_str.split(':')

            formatted_time = (
                f"{int(h):03d}:{m}:{s}"
            )

            # 유동 보스는 젠 정보 뒤에 별도 표기 추가
            fluid_text = " (유동 젠)" if "," in info['time'] else ""

            msg += (
                f"⏱️ 젠 타임 : "
                f"[{formatted_time}]  -  "
                f"👹 {name}({info['alias']}){fluid_text}\n"
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
    if content in ["보스탐", "현황", "보스","보탐"]:

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
    if content in ("메뉴얼", "명령어"):

        manual = (
            "🎮 아이모 보스탐 매니저 v1.4\n\n"

            "═════════════════\n"
            "📋 [보스 관리]\n"
            "═════════════════\n\n"

            "📋 보스목록 조회\n"
            "`보스목록` 또는 `보스`\n"
            "• 전체 등록 보스 및 기본 젠 타임 확인\n\n"

            "➕ 보스 등록\n"
            "`보스등록 02:30:00 여왕(ㅇㅇ)`\n"
            "• 형식: 시간(HH:MM:SS) 보스명(약어)\n"
            "• 유동 젠 보스는 콤마로 연달아 등록 (예: 02:53:00,02:43:00,02:30:00)\n"
            "• 커스텀 보스 추가 및 재시작 시 유지\n\n"

            "🗑️ 보스목록 삭제\n"
            "`보스삭제 깬`\n"
            "• 보스를 디비 목록에서 완전히 삭제\n"
            "• 기본 패키지 보스는 보호됨\n\n"

            "═════════════════\n"
            "⚔️ [보스 타이밍 관리]\n"
            "═════════════════\n\n"

            "⚔️ 보스 컷 기록 (실시간 및 과거)\n"
            "`와당컷`, `ㅇㄷㅋ` 또는 `1304 와당컷`, `와당컷 13:04`\n"
            "• 과거 시간은 1304, 13:04, 13:04:30 형식 지원\n"
            "• 과거 시간 입력은 누락 횟수에 포함하지 않고 다음 미래 젠 계산\n"
            "• 유동 보스는 컷 입력마다 다음 회차 젠타임 자동 적용\n\n"

            "⏱️ 확정 젠 타임 등록\n"
            "`12:12:00 깬 젠` 또는 `깬 12:12 젠`\n"
            "• 여러 줄을 한 번에 입력해 여러 보스 등록 가능\n"
            "• 확정 젠 등록 후 유동 보스는 마지막 젠 시간을 계속 사용\n\n"

            "❌ 현황에서 삭제\n"
            "`깬삭제` 또는 `깬 삭제`\n"
            "• 특정 보스를 현황판 예약에서만 제거\n\n"

            "🗑️ 현황에서 전체삭제\n"
            "`전체삭제` 또는 `초기화`\n"
            "• 예약판 전체를 비우고 유동 회차 카운트를 첫 번째 타임부터 재시작\n\n"

            "🔴 자동 삭제 (미입력 3회 방치)\n"
            "• 컷 미입력 상태로 3회 연속 자동 연장 시 현황 자동 청소\n\n"

            "═════════════════\n"
            "📊 [현황 조회 및 시스템]\n"
            "═════════════════\n\n"

            "📊 현재 보스 현황\n"
            "`보스탐`, `현황` 또는 `보탐`\n"
            "• 예약 완료된 보스별 젠 예정 시각 리스트\n"
            "• 미입력 연장 횟수 및 미예약 보스 일괄 조회\n\n"

            "📚 고정 스케줄 알림\n"
            "• 매일 지정된 시각에 맞춰 금서고 타임 알림 자동 제어\n"
            "• 10분 전 / 5분 전 / 1분 전 / 정각 타임 순차 작동\n\n"

            "═════════════════"
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

        # 유동적 등록(콤마 포함) 및 단일 시간 형식의 검증이 가능하도록 정규식 분기 완화
        if not re.match(r'^[\d{1,2}:\d{2}:\d{2},?]+$', time_str):

            await message.channel.send(
                "❌ 시간 형식 오류\n"
                "예시: 02:30:00 또는 유동젠은 02:53:00,02:30:00"
            )

            return

        # 보스이름(약어) 파싱
        match = re.match(r'(.+?)\((.+?)\)', boss_info_str)

        if not match:

            await message.channel.send(
                "❌ 형식 오류\n"
                "예시: `보스등록 02:30:00 여왕(ㅇㅇ)`"
            )

            return

        boss_name = match.group(1).strip()

        boss_alias = match.group(2).strip()

        if save_custom_boss(boss_name, time_str, boss_alias):

            await message.channel.send(
                f"✅ 보스 등록 완료!\n"
                f"• 보스명: {boss_name}\n"
                f"• 약어: {boss_alias}\n"
                f"• 젠 타임: {time_str}"
            )

        else:

            await message.channel.send(
                "❌ 보스 저장에 실패했습니다."
            )

        return

    # =====================
    # 보스목록 완전 삭제
    # =====================
    if content.startswith("보스삭제"):

        target_name = content.replace("보스삭제", "").strip()

        if not target_name:

            await message.channel.send(
                "❌ 삭제할 보스명 또는 약어를 입력해주세요.\n"
                "예시: `보스삭제 깬`"
            )

            return

        found_boss = None

        for name, info in BOSS_DATA.items():

            if name == target_name or info['alias'] == target_name:

                found_boss = name

                break

        if not found_boss:

            await message.channel.send(
                "❌ 등록되지 않은 보스입니다."
            )

            return

        if delete_custom_boss(found_boss):

            await message.channel.send(
                f"🗑️ 커스텀 보스 `[{found_boss}]`가 "
                f"목록에서 완전히 삭제되었습니다."
            )

        else:

            await message.channel.send(
                "❌ 삭제 실패: 기본 보스는 삭제할 수 없거나 "
                "오류가 발생했습니다."
            )

        return

    # =====================
    # 삭제 및 전체 삭제 처리
    # =====================
    if content in ["전체삭제", "초기화"]:

        storage.boss_timers.clear()

        storage.extend_counts.clear()

        if hasattr(storage, 'cut_counts'):

            storage.cut_counts.clear()

        if hasattr(storage, 'notified_records'):

            storage.notified_records.clear()

        await message.channel.send(
            "🧹 모든 보스 현황 데이터가 전체 삭제되었습니다."
        )

        return

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
                hasattr(storage, 'cut_counts')
                and target_boss in storage.cut_counts
            ):
                del storage.cut_counts[target_boss]

            if (
                hasattr(storage, 'notified_records')
                and target_boss in storage.notified_records
            ):
                del storage.notified_records[
                    target_boss
                ]

            storage.extend_counts[target_boss] = 0

            await message.channel.send(
                f"❌ {target_boss} 삭제 완료"
            )

        return
