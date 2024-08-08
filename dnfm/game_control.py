import time
import math
import random
from typing import Tuple
import pygetwindow as gw
from scrcpy_adb_qt import scrcpyQt


class GameControl:
    def __init__(self, adb: scrcpyQt, window_title: str):
        self.user = "NM"
        self.window_title = window_title
        self.adb = adb
        self.get_window_xy()
        self.skill_coordinates = {
            "Y": [(0.49, 0.87), (0.71, 0.77), (0.74, 0.88), (0.84, 0.77)],
            "J": [(0.62, 0.88), (0.68, 0.88), (0.77, 0.77), (0.65, 0.77)],
            "JX": [(0.407, 0.9)],
            "Buff": [(0.87, 0.67)],
            "Buff2": [(0.87, 0.67)]
        }
        self.skill_mapping = {
            # 0大锤、1领悟之雷、2往前推的盾、3矛、4唱小歌、5禁锢锁链、6挥三棒、7沐天之光、
            "NM": [
                (0.49, 0.87), (0.54, 0.90), (0.62, 0.88), (0.68, 0.9),
                (0.65, 0.79), (0.72, 0.78), (0.78, 0.796), (0.83, 0.78)
            ],
            # 0鬼影闪、1四阵、2鬼影剑、3鬼影鞭、4冥炎三、5鬼斩、6鬼月绝、7墓碑、
            "GQ": [
                (0.68, 0.9), (0.72, 0.78), (0.62, 0.88), (0.78, 0.796),
                (0.83, 0.78), (0.72, 0.78), (0.65, 0.79), (0.54, 0.90)
            ]
        }
        self.level = 0

    def calc_mov_point(self, angle: float) -> Tuple[int, int]:
        rx, ry = (
            self.windowsInfo[0] + (self.windowsInfo[2] * 0.1646),
            self.windowsInfo[1] + (self.windowsInfo[3] * 0.7198)
        )
        r = self.windowsInfo[2] * 0.055
        x = rx + r * math.cos(math.radians(angle))
        y = ry - r * math.sin(math.radians(angle))
        return int(x), int(y)

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
            time.sleep(0.1)
        self.adb.touch_end(x, y)

    def get_center_xy(self) -> Tuple[int, int]:
        x = self.windowsInfo[0] + (self.windowsInfo[2] * 0.5)
        y = self.windowsInfo[1] + (self.windowsInfo[3] * 0.5)
        print(f"Center point: ({x}, {y})")
        return int(x), int(y)

    def attack(self, t: float = 0.01):
        self._perform_attack(
            (self.windowsInfo[0] + (self.windowsInfo[2] * 0.87),
             self.windowsInfo[1] + (self.windowsInfo[3] * 0.89)),
            t
        )

    def attack_y(self, t: float = 0.01):
        self._perform_skill_attack("Y", t)

    def attack_j(self, t: float = 0.01):
        self._perform_skill_attack("J", t)

    def attack_jx(self, t: float = 0.01):
        x, y = self._get_skill_position("JX", 0)
        for _ in range(4):
            self.adb.tap(x, y)

    def _perform_attack(self, position: Tuple[int, int], t: float):
        x, y = position
        for _ in range(2):
            self.adb.touch_start(x, y)
        time.sleep(t)
        self.adb.touch_end(x, y)

    def _perform_skill_attack(self, skill_type: str, t: float):
        skill = random.choice(self.skill_coordinates[skill_type])
        x, y = (self.windowsInfo[0] + (self.windowsInfo[2] * skill[0]),
                self.windowsInfo[1] + (self.windowsInfo[3] * skill[1]))
        self._perform_attack((x, y), t)

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
            "GQ": self.gq_fixed
        }
        if self.user in fixed_methods:
            fixed_methods[self.user](room_num)
        else:
            raise ValueError("Unknown user type")

    def _get_skill_position(self, skill_type: str, skill_num: int) -> Tuple[int, int]:
        skill = self.skill_mapping[self.user][skill_num]
        x, y = (self.windowsInfo[0] + (self.windowsInfo[2] * skill[0]),
                self.windowsInfo[1] + (self.windowsInfo[3] * skill[1]))
        self.adb.tap(x, y)
        self.adb.tap(x, y)
        return x, y

    def add_buff(self, t: float = 0.01, direction: str = "down"):
        x, y = (self.windowsInfo[0] + (self.windowsInfo[2] * self.skill_coordinates["Buff"][0][0]),
                self.windowsInfo[1] + (self.windowsInfo[3] * self.skill_coordinates["Buff"][0][1]))
        self.adb.touch_start(x, y)
        self.adb.touch_move(x, y - 35 if direction == "down" else y + 35)
        self.adb.touch_end(x, y)

    def click_again(self):
        self.adb.tap(0.86, 0.25)

    def get_item_height(self) -> float:
        return self.windowsInfo[3] * 0.07

    def click_map(self):
        self.adb.tap(0.90, 0.186)

    def get_map_xy(self) -> Tuple[float, float, float, float]:
        return (self.windowsInfo[2] * 0.380, self.windowsInfo[3] * 0.380,
                self.windowsInfo[2] * 0.629, self.windowsInfo[3] * 0.637)

    def get_window_xy(self):
        try:
            window = gw.getWindowsWithTitle(self.window_title)[0]
            if window:
                window.restore()
                window.activate()
                time.sleep(0.5)
                self.windowsInfo = (window.left, window.top, window.width, window.height)
        except Exception as e:
            print(f"Window not found: {e}")

    def nm_fixed(self, room_num: int):
        fixed_moves = {
            0: [5, 7],
            7: [(0, 0.1), 2, 6, (270, 0.5), 4],
            13: [2, 6],
            14: [5, 0],
            15: [(90, 0.3), 4],
            9: "Awaken",
            8: [2, 1, 3],
            10: [2, 1],
            11: [5, 0]
        }
        self._execute_fixed_moves(fixed_moves, room_num)

    def gq_fixed(self, room_num: int):
        fixed_moves = {
            0: [("Buff2",), 0],
            7: [2, (0, 0.1), 7, 3, (0, 0.2), 1, 1],
            13: [2, 3],
            14: [1, 1, 3],
            15: [(90, 0.3), 7],
            9: "Awaken",
            8: [(0, 0.2), 0, 7],
            10: [2, 3],
            11: [(0, 0.4), 4, 7]
        }
        self._execute_fixed_moves(fixed_moves, room_num)

    def _execute_fixed_moves(self, fixed_moves: dict, room_num: int):
        moves = fixed_moves.get(room_num)
        if moves:
            for move in moves:
                if isinstance(move, tuple):
                    self.move(*move)
                elif isinstance(move, str) and move == "Awaken":
                    print("Use awakening in lion room")
                else:
                    self._get_skill_position(self.user, move)
        else:
            print(f"No fixed moves defined for room {room_num}")


if __name__ == '__main__':
    window_title = "Phone-f0d62d51"
    ctl = GameControl(scrcpyQt(window_title), window_title)
    ctl.get_window_xy()
    ctl.attack_fixed(1)
