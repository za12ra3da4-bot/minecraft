"""보스 공용 데이터 — 리소스팩(보스바 라벨) · 데이터팩 · Skript 생성기가 함께 쓴다"""

BOSSES = {
    "talos": {
        "name": "청동 골렘",
        "short": "골렘",
        "lair": "forge",
        "style": "돌진·직선형",
        "hp": 1900,
        "skills": {
            "rush": "청동 돌진",
            "fissure": "대지 가르기",
            "overheat": "용광로 폭주",
        },
    },
    "sphinx": {
        "name": "스핑크스",
        "short": "스핑크스",
        "lair": "sands",
        "style": "광역 마법진·석화형",
        "hp": 1700,
        "skills": {
            "riddle": "석화의 수수께끼",
            "sandmark": "모래 표식",
            "seal": "봉인의 고리",
        },
    },
    "ladon": {
        "name": "히드라",
        "short": "히드라",
        "lair": "garden",
        "style": "다중 지점·순차형",
        "hp": 2000,
        "skills": {
            "storm": "백두 폭풍",
            "venom": "독 숨결",
            "apple": "황금 사과의 재생",
        },
    },
    "cyclops": {
        "name": "사이클롭스",
        "short": "사이클롭스",
        "lair": "quarry",
        "style": "근접 광역·추적형",
        "hp": 2200,
        "skills": {
            "quake": "대지 진동",
            "boulder": "거암 추격",
            "whirl": "회전 강타",
        },
    },
}


# 이벤트 보스 — 미니 보스 목록(무작위 소환 · a03)에는 안 들어가고, 보스바 이름판 · 초상화 글리프만 만든다
EXTRA_BOSSES = {
    "nemesis": {
        "name": "네메시스",
        "skills": {
            "verdict": "심판의 검",
            "scales": "응보의 저울",
            "wings": "날개 폭풍",
        },
    },
}


# 맵 전용 보스 (빙하 왕국 · 화산 군도) — 미니 보스처럼 투기장에서 소환되지만, 맵마다 나오는 보스 목록은 a42 {-bg::mapboss::<맵>::*}
#  보스바 글리프는 네메시스 뒤에 덧붙여 기존 글리프 번호가 바뀌지 않게
MAP_BOSSES = {
    "ymir": {
        "name": "서리 거인 이미르",
        "short": "이미르",
        "lair": "quarry",
        "style": "광역·빙결형",
        "hp": 2400,
        "skills": {"glacier": "빙하 붕괴", "avalanche": "눈사태", "zero": "절대 영도"},
    },
    "fenrir": {
        "name": "서리 늑대 펜리르",
        "short": "펜리르",
        "lair": "garden",
        "style": "기동·추적형",
        "hp": 2000,
        "skills": {"pounce": "서리 도약", "frostbreath": "빙결 포효", "fangs": "얼음 송곳니"},
    },
    "surtr": {
        "name": "화염 거인 수르트",
        "short": "수르트",
        "lair": "forge",
        "style": "광역·화염형",
        "hp": 2600,
        "skills": {"doom": "멸망의 검", "meteor": "화염 비", "ragnarok": "라그나로크"},
    },
    "cerberus": {
        "name": "지옥견 케르베로스",
        "short": "케르베로스",
        "lair": "sands",
        "style": "돌진·화염형",
        "hp": 2200,
        "skills": {"charge": "지옥 돌진", "triflame": "삼두 화염", "lavapool": "용암 웅덩이"},
    },
}
