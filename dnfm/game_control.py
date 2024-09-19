import time
import math
import random
from typing import Tuple
import pygetwindow as gw
from .scrcpy_adb_qt import ScrcpyADB


class GameControl:
    def __init__(self, adb: ScrcpyADB):
        self.user = "KZ"
        # left, top是窗口左上角的坐标
        # width, height是窗口的宽度和高度
        self.windowsInfo = [0, 0, 2400, 1080]
        self.adb = adb
        self.get_window_xy()
        self.combine_num = 0
        self.skill_coordinates = {
            "Y": [(1193, 967), (1193, 967), (1306, 967), (1502, 967)],
            "J": [(1563, 844), (1713, 844), (1887, 844), (2011, 844)],
            "JX": [(976, 967)],
            "Buff": [(2104, 723)],
            "Buff2": [(2104, 723)]
        }

        self.skill_mapping = {
            # 0大锤、1领悟之雷、2往前推的盾、3矛、4唱小歌、5禁锢锁链、6挥三棒、7沐天之光、
            "NM": [
                (1193, 973), (1298, 973), (1502, 973), (1643, 973),
                (1563, 844), (1713, 844), (1887, 844), (2011, 844)
            ],
            # 0鬼影闪、1四阵、2鬼影剑、3鬼影鞭、4冥炎三、5鬼斩、6鬼月绝、7墓碑、
            "GQ": [
                (1643, 973), (1713, 844), (1502, 973),  (1887, 844),
                (2011, 844), (1797, 973), (1563, 844), (1298, 973),
            ],
            # 0崩山击，1 三段斩， 2怒气，3大吸，4小吸，5打崩，6血剑，7狂斩
            "KZ": [
                (1806, 968), (1298, 973), (1502, 973), (1643, 973),
                (1563, 844), (1713, 844), (1887, 844), (2011, 844)
            ],
            # 0 落火 1 地裂喷起来 2 反坦克 3 喷火器 4 激光炮  5 压缩 6 量子爆弹 7 榴弹
            "QP": [
                (1193, 973), (1298, 973), (1502, 973), (1643, 973),
                (1563, 844), (1093, 973), (1887, 844), (2011, 844)
            ]
        }
        self.level = 0

    def calc_mov_point(self, angle: float) -> Tuple[int, int]:
        rx, ry = (
            394,
            777
        )
        r = 133
        x = rx + r * math.cos(math.radians(angle))
        y = ry - r * math.sin(math.radians(angle))
        return int(x), int(y)

    def click(self, x, y, t: float = 0.01):
        x, y = self._ramdon_xy(x, y)
        self.adb.touch_start(x, y)
        time.sleep(t)
        self.adb.touch_end(x, y)

    def _ramdon_xy(self, x, y):
        x = x + random.randint(-5, 5)
        y = y + random.randint(-5, 5)
        return x, y

    def move(self, angle: float, t: float):
        x, y = self.calc_mov_point(angle)
        self.adb.touch_start(x, y)
        time.sleep(t)
        self.adb.touch_end(x, y)

    def moveLU(self):
        self._move_sequence([180, 90])

    def moveRD(self):
        self._move_sequence([0, 270])

    def _move_sequence(self, angles: list):
        for angle in angles:
            x, y = self.calc_mov_point(angle)
            self.adb.touch_start(x, y)
            time.sleep(2)
        self.adb.touch_end(x, y)

    def get_center_xy(self) -> Tuple[int, int]:
        x = self.windowsInfo[0] + (self.windowsInfo[2] * 0.5)
        y = self.windowsInfo[1] + (self.windowsInfo[3] * 0.5)
        print(f"Center point: ({x}, {y})")
        return int(x), int(y)

    def attack(self, t: float = 0.01):
        for _ in range(2):
            self.adb.tap(2099, 969)
            time.sleep(0.1)

    def attack_y(self, t: float = 0.01):
        self._perform_skill_attack("Y", t)

    def attack_j(self, t: float = 0.01):
        self._perform_skill_attack("J", t)

    def attack_jx(self, t: float = 0.01):
        x, y = self.skill_coordinates["JX"][0]
        for _ in range(6):
            self.adb.tap(x, y)
            time.sleep(0.3)

    def _perform_skill_attack(self, skill_type: str, t: float):
        skill = random.choice(self.skill_coordinates[skill_type])
        self.adb.tap(skill[0], skill[1])

    def attack_combine(self, num: int):
        num += self.level
        if num == 1:
            self.attack()
        elif num < 3:
            self.attack_j()
            self.attack()
        elif num <= 7:
            self.attack_y()
            self.attack()
        else:
            self.attack_j()

    def attack_fixed(self, room_num: int):
        print(f"Fixed attack for room {room_num}")
        fixed_methods = {
            "NM": self.nm_fixed,
            "GQ": self.gq_fixed,
            "KZ": self.kz_fixed,
            "QP": self.qp_fixed,
        }
        if self.user in fixed_methods:
            fixed_methods[self.user](room_num)
        else:
            raise ValueError("Unknown user type")

    def _get_skill_position(self, skill_num: int, t: float = 0.3) -> Tuple[int, int]:
        skill = self.skill_mapping[self.user][skill_num]

        self.adb.tap(skill[0], skill[1], t)
        self.adb.tap(skill[0], skill[1], t)
        time.sleep(0.1)
        return skill[0], skill[1]

    def add_buff(self, buffNum: int = 1):
        x, y = self.skill_coordinates["Buff"][0]
        self.adb.touch_start(x, y)
        time.sleep(0.3)
        # 根据方向移动坐标
        if buffNum == 1:
            self.adb.touch_move(x, y - 60)  # 往上移动35像素
        else:
            self.adb.touch_move(x, y + 60)  # 往下移动35像素
        time.sleep(0.3)
        # 放开
        self.adb.touch_end(x, y)

    def click_again(self):
        self.adb.tap(0.86, 0.25)

    def get_item_height(self) -> float:
        return self.windowsInfo[3] * 0.07

    def click_map(self):
        self.adb.tap(2173, 104)

    def get_map_xy(self) -> Tuple[float, float, float, float]:
        return (884, 389, 1514, 694)

    def get_window_xy(self):
        try:
            self.windowsInfo = [0, 0, 2400, 1080]
        except Exception as e:
            print(f"Window not found: {e}")

    # 0大锤、1领悟之雷、2往前推的盾、3矛、4唱小歌、5禁锢锁链、6挥三棒、7沐天之光、

    def nm_fixed(self, roomNum: int):
        if roomNum == 7:
            time.sleep(0.1)
            self.add_buff(1)
            time.sleep(0.2)
            self._get_skill_position(6)
            time.sleep(0.3)
            self._get_skill_position(1)
            time.sleep(2.5)
        elif roomNum == 13:
            time.sleep(0.1)
            # self.move(270, 0.2)
            # time.sleep(0.1)
            # self.move(270, 0.3)
            self._get_skill_position(7)
            time.sleep(0.1)
            self._get_skill_position(2)
            time.sleep(0.3)
        elif roomNum == 14:
            time.sleep(0.2)
            # self.move(270, 0.1)
            # time.sleep(0.2)
            # self.move(300, 0.2)
            self._get_skill_position(3, 0.7)
            time.sleep(0.5)
            self._get_skill_position(3)
            time.sleep(0.2)
        elif roomNum == 15:
            time.sleep(0.2)
            # self.move(0, 0.2)
            # time.sleep(0.1)
            # self.move(0, 0.3)
            time.sleep(0.1)
            self._get_skill_position(4)
            time.sleep(0.5)
        elif roomNum == 9:
            time.sleep(0.1)
            # self.move(30, 0.6)
            # time.sleep(0.1)
            # self.move(180, 0.1)
            self._get_skill_position(2)
            time.sleep(0.1)
            self._get_skill_position(6)
            self.move(180, 2)
        elif roomNum == 8:
            print("狮子房间使用觉醒")
            self.attack_jx()
        elif roomNum == 10:
            time.sleep(0.1)
            # self.move(0, 0.2)
            self._get_skill_position(2)
            time.sleep(0.2)
            self._get_skill_position(1)
            time.sleep(0.2)
        elif roomNum == 11:
            # time.sleep(0.5)
            # self.move(0, 0.2)
            # time.sleep(0.1)
            # self.move(0, 0.3)
            time.sleep(0.2)
            self._get_skill_position(6)
            time.sleep(0.2)
            self._get_skill_position(3)
            time.sleep(0.3)
            self._get_skill_position(3)
            time.sleep(0.2)
        elif roomNum == 12:
            time.sleep(0.2)
            print("进入boss")
            self._get_skill_position(4)
            # time.sleep(0.5)
            # self._get_skill_position(0)
            time.sleep(5)

    # 0鬼影闪、1四阵、2鬼影剑、3鬼影鞭、4冥炎三、5鬼斩、6鬼月绝、7墓碑
    def gq_fixed(self, roomNum: int):
        skills_combine = [
            [0, 1],
            [3, 6],
            [7],
            [1, 1],
            [4],
            [2]
        ]

        if roomNum == 7:
            self.add_buff(1)
            time.sleep(0.2)
            self.add_buff(2)

        if  roomNum == 8:
            time.sleep(0.1)
            self.move(270, 0.2)
            time.sleep(0.2)
            self.attack_jx()
        for i in skills_combine[self.combine_num % 6]:
            self._get_skill_position(i)
            time.sleep(0.2)
        self.combine_num += 1    


       # 0崩山击，1 三段斩， 2怒气，3大吸，4小吸，5打崩，6血剑，7狂斩
    def kz_fixed(self, roomNum: int):
        if roomNum == 7:
            self.add_buff(1)
            # self.add_buff(2)
            time.sleep(0.1)
            # self.move(0, 0.6)
            self._get_skill_position(7)
            time.sleep(0.1)
        elif roomNum == 13:
            time.sleep(0.1)
            # self.move(315, 0.2)
            # time.sleep(0.1)
            # self.move(315, 0.4)
            self._get_skill_position(3, 1)
            time.sleep(0.1)
        elif roomNum == 14:
            time.sleep(0.2)
            self._get_skill_position(2)
            self.attack()
        elif roomNum == 15:
            time.sleep(0.1)
            # self.move(0, 0.3)
            self._get_skill_position(2)
            self.attack()
        elif roomNum == 9:
            time.sleep(0.1)
            self._get_skill_position(5)
            time.sleep(0.1)
            self.move(180, 2)
        elif roomNum == 8:
            time.sleep(0.1)
            self.move(270, 0.2)
            self.attack_jx()
            self.move(180, 0.5)
        elif roomNum == 10:
            time.sleep(0.1)
            # self.move(0, 0.2)
            self._get_skill_position(0)
            time.sleep(0.1)
            self._get_skill_position(2)
            time.sleep(0.3)
            self._get_skill_position(6)
            time.sleep(0.3)
        elif roomNum == 11:
            time.sleep(0.1)
            # self.move(0, 0.2)
            # time.sleep(0.1)
            # self.move(0, 0.4)
            self._get_skill_position(7)
            time.sleep(2)
        elif roomNum == 12:
            print("进入boss")
            time.sleep(0.1)
            # self.move(0, 0.7)
            self._get_skill_position(5)
            time.sleep(5)

    # 0 落火 1 地裂喷起来 2 反坦克 3 喷火器 4 激光炮  5 压缩 6 量子爆弹 7 榴弹
    def qp_fixed(self, roomNum: int):
        if roomNum == 7:
            self.add_buff(1)
            time.sleep(0.1)
            self.add_buff(2)
            time.sleep(0.1)
            self._get_skill_position(4, 1)
            time.sleep(0.1)
        elif roomNum == 13:
            time.sleep(0.1)
            self.move(270, 0.2)
            time.sleep(0.1)
            self.move(270, 0.3)
            self._get_skill_position(1)
            time.sleep(0.1)
        elif roomNum == 14:
            time.sleep(1)
            self._get_skill_position(0)
            time.sleep(0.1)
        elif roomNum == 15:
            time.sleep(0.1)
            self._get_skill_position(4, 1)
            time.sleep(0.5)
            self.move(0, 0.5)
            time.sleep(0.5)
            self._get_skill_position(6)
            time.sleep(0.1)
        elif roomNum == 9:
            time.sleep(0.1)
            self.move(30, 0.6)
            time.sleep(0.1)
            self.move(180, 0.1)
            self._get_skill_position(5, 2)
            time.sleep(0.1)
            self.move(180, 2)
        elif roomNum == 8:
            time.sleep(0.1)
            self.move(180, 0.2)
            time.sleep(0.1)
            self.move(180, 0.2)
            self.attack_jx()
            time.sleep(0.6)
            self._get_skill_position(2)
            time.sleep(2)
        elif roomNum == 10:
            time.sleep(0.1)
            self.move(0, 0.2)
            time.sleep(0.1)
            self.move(270, 0.2)
            self._get_skill_position(4, 1)
            time.sleep(0.3)
        elif roomNum == 11:
            time.sleep(0.3)
            time.sleep(0.3)
            self._get_skill_position(7)
            time.sleep(0.6)
            self._get_skill_position(2)
        elif roomNum == 12:
            print("进入boss")
            time.sleep(0.3)
            time.sleep(0.3)
            self._get_skill_position(5, 2)
            time.sleep(5)


if __name__ == '__main__':
    ctl = GameControl(ScrcpyADB(2400))
    ctl.get_window_xy()
    ctl.attack()
