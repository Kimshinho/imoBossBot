import json
import os

BOSS_DATA = {
    "깬": {"time": "01:03:00", "alias": "ㄲ"},
    "여왕": {"time": "02:30:00", "alias": "ㅇㅇ"},
    "와당": {"time": "02:30:00", "alias": "ㅇㄷ"},
    "페": {"time": "05:52:00", "alias": "ㅍ"},
    "악타": {"time": "06:00:00", "alias": "ㅇㅌ"},
    "소울": {"time": "24:15:00", "alias": "ㅅㅇ"},
    "바슬": {"time": "48:00:00", "alias": "ㅄ"},
    "빅마": {"time": "48:00:00", "alias": "ㅂㅁ"},
    "우크": {"time": "48:00:00", "alias": "ㅇㅋ"},
    "딜린": {"time": "72:00:00", "alias": "ㄷㄹ"},
    "세피아": {"time": "72:00:00", "alias": "ㅅㅍ"},
    "일루": {"time": "72:00:00", "alias": "ㅇㄹ"},
    "칼리고": {"time": "168:00:00", "alias": "ㅋㄹ"},
    "오버로드": {"time": "00:30:00", "alias": "ㅇㅂ"}
}

CUSTOM_BOSS_FILE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "custom_bosses.json"
)

def load_custom_bosses():
    """커스텀 보스 데이터 로드"""
    if os.path.exists(CUSTOM_BOSS_FILE):
        try:
            with open(CUSTOM_BOSS_FILE, 'r', encoding='utf-8') as f:
                custom = json.load(f)
                BOSS_DATA.update(custom)
        except Exception as e:
            print(f"⚠️ 커스텀 보스 로드 실패: {e}")

# 봇 시작시 커스텀 보스 로드
load_custom_bosses()
