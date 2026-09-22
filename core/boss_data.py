import json
import os

BOSS_DATA = {

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
