"""전장 배치 상수 — 모든 좌표는 맵 로컬 (x, z) = 0..255, y = 0..95

        N (레드 본진)
   NW 데메테르 제단      NE 아레스 제단
 W (옐로)     중앙 대신전      E (블루)
   SW 헤르메스 제단      SE 아테나 제단
        S (그린 본진)

 네 모서리 = 보스 전용 투기장 (라돈 / 탈로스 / 스핑크스 / 키클롭스)
"""
import math

SIZE = 256
HEIGHT = 96
G = 24                          # 기본 지면 높이 (로컬 y)
C = (128, 128)                  # 맵 중심
ORIGIN = (-128, 40, -128)       # 기본 월드 좌표 원점 → 지면 = 월드 y 64

TEAMS = {
    # id: (방향 단위벡터 (dx,dz), 이름, 색 코드, 양털/색 블록 접두사)
    "red":    ((0, -1), "레드", "c", "red"),
    "blue":   ((1, 0), "블루", "9", "blue"),
    "green":  ((0, 1), "그린", "a", "lime"),
    "yellow": ((-1, 0), "옐로", "e", "yellow"),
}
TEAM_ORDER = ["red", "blue", "green", "yellow"]
BASE_DIST = 100
BASE_R = 24
BASE_H = G + 5

ALTARS = {
    # id: (방향 (dx,dz), 이름, 테마)
    "ares":    ((1, -1), "아레스의 제단", "war"),
    "athena":  ((1, 1), "아테나의 제단", "wisdom"),
    "hermes":  ((-1, 1), "헤르메스의 제단", "wind"),
    "demeter": ((-1, -1), "데메테르의 제단", "harvest"),
}
ALTAR_OFF = 60                  # 중심에서 대각선으로 (±60, ±60)

LAIRS = {
    # id: (방향, 보스, 이름)
    "forge":  ((1, -1), "talos", "헤파이스토스의 대장간"),
    "sands":  ((1, 1), "sphinx", "잊힌 모래 신전"),
    "quarry": ((-1, 1), "cyclops", "거인의 채석장"),
    "garden": ((-1, -1), "ladon", "헤스페리데스의 정원"),
}
LAIR_OFF = 94
LAIR_R = 19

PLAZA_R = 36
MOAT_IN = 43
MOAT_OUT = 49


def team_base(t):
    (dx, dz) = TEAMS[t][0]
    return (C[0] + dx * BASE_DIST, C[1] + dz * BASE_DIST)


def altar_pos(a):
    (dx, dz) = ALTARS[a][0]
    return (C[0] + dx * ALTAR_OFF, C[1] + dz * ALTAR_OFF)


def lair_pos(l):
    (dx, dz) = LAIRS[l][0]
    return (C[0] + dx * LAIR_OFF, C[1] + dz * LAIR_OFF)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])
