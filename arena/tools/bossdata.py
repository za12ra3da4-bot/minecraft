"""보스 공용 데이터 — 리소스팩(보스바 라벨) · 데이터팩 · Skript 생성기가 함께 쓴다"""

BOSSES = {
    "talos": {
        "name": "청동 거신",
        "short": "거신",
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
        "name": "사막 석사자",
        "short": "석사자",
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
        "name": "구두룡",
        "short": "구두룡",
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
        "name": "외눈 산귀",
        "short": "산귀",
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
