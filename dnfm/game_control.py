import time
from typing import Tuple
import pygetwindow as gw
from scrcpy_adb_qt import scrcpyQt
import math
import random


class GameControl:
    def __init__(self, adb: scrcpyQt, window_title):
        # 奶妈 NM 、 鬼泣 GQ
        self.user = "NM"
        self.level = 0
        self.window_title = window_title
        self.adb = adb
        self.get_window_xy()
        self.skillY = [
            (0.49, 0.87), (0.71, 0.77), (0.74, 0.88), (0.84, 0.77)
        ]
        self.skillJ = [
            (0.62, 0.88), (0.68, 0.88), (0.77, 0.77), (0.65, 0.77)
        ]
        self.skillJX = [
            (0.407, 0.9)
        ]
        self.skillBuff = [
            (0.87, 0.67)
        ]
        self.skillBuff2 = [
            (0.87, 0.67)
        ]
        # 0大锤、1领悟之雷、2往前推的盾、3矛、4唱小歌、5禁锢锁链、6挥三棒、7沐天之光、
        self.skillNM = [
            (0.49, 0.87), (0.54, 0.90), (0.62, 0.88), (0.68, 0.9), (0.65,
                                                                    0.79), (0.72, 0.78), (0.78, 0.796), (0.83, 0.78)
        ]
        # 0鬼影闪、1四阵、2鬼影剑、3鬼影鞭、4冥炎三、5鬼斩、6鬼月绝、7墓碑、
        self.skillGQ = [
            (0.68, 0.9), (0.72, 0.78), (0.62, 0.88), (0.78, 0.796), (0.83,
                                                                     0.78), (0.72, 0.78), (0.65,
                                                                                           0.79), (0.54, 0.90)
        ]

    def calc_mov_point(self, angle: float) -> Tuple[int, int]:
        rx, ry = (self.windowsInfo[0] + (self.windowsInfo[2] * 0.1646),
                  self.windowsInfo[1] + (self.windowsInfo[3] * 0.7198))
        r = self.windowsInfo[2] * 0.055

        x = rx + r * math.cos(angle * math.pi / 180)
        y = ry - r * math.sin(angle * math.pi / 180)
        return int(x), int(y)

    def move(self, angle: float, t: float):
        # 计算轮盘x, y坐标
        x, y = self.calc_mov_point(angle)
        self.adb.touch_start(x, y)
        time.sleep(t)
        self.adb.touch_end(x, y)

    # 左上
    def moveLU(self):
        x, y = self.calc_mov_point(180)
        self.adb.touch_start(x, y)
        time.sleep(0.1)
        x, y = self.calc_mov_point(90)
        self.adb.touch_start(x, y)
        time.sleep(0.1)
        self.adb.touch_end(x, y)

    # 右下
    def moveRD(self):
        x, y = self.calc_mov_point(0)
        self.adb.touch_start(x, y)
        time.sleep(0.1)
        x, y = self.calc_mov_point(270)
        self.adb.touch_start(x, y)
        time.sleep(0.1)
        self.adb.touch_end(x, y)

    def getCenterXY(self):
        x, y = ((self.windowsInfo[2] * 0.5),
                (self.windowsInfo[3] * 0.5))
        print("zdian" + str(x) + "," + str(y))
        return int(x), int(y)

    def attack(self, t: float = 0.01):
        x, y = (self.windowsInfo[0] + (self.windowsInfo[2] * 0.87),
                self.windowsInfo[1] + (self.windowsInfo[3] * 0.89))
        for _ in range(2):
            self.adb.touch_start(x, y)
        time.sleep(t)
        self.adb.touch_end(x, y)

    def attackY(self, t: float = 0.01):
        skill = random.choice(self.skillY)
        x, y = (self.windowsInfo[0] + (self.windowsInfo[2] * skill[0]),
                self.windowsInfo[1] + (self.windowsInfo[3] * skill[1]))
        for _ in range(2):
            self.adb.touch_start(x, y)
        time.sleep(t)
        self.adb.touch_end(x, y)

    def attackJ(self, t: float = 0.01):
        skill = random.choice(self.skillJ)
        x, y = (self.windowsInfo[0] + (self.windowsInfo[2] * skill[0]),
                self.windowsInfo[1] + (self.windowsInfo[3] * skill[1]))
        for _ in range(2):
            self.adb.touch_start(x, y)
        time.sleep(t)
        self.adb.touch_end(x, y)

    def attackJX(self, t: float = 0.01):
        x, y = (self.windowsInfo[0] + (self.windowsInfo[2] * self.skillJX[0][0]),
                self.windowsInfo[1] + (self.windowsInfo[3] * self.skillJX[0][1]))
        for _ in range(4):
            self.adb.tap(x, y)

    def attackCombine(self, num: int):
        num += self.level
        if num == 1:
            for _ in range(2):
                self.attack()
        elif num < 3:
            self.attackJ()
            for _ in range(2):
                self.attack()
        elif num <= 7:
            self.attackY()
            for _ in range(2):
                self.attack()
            # self.attackJ()
        else:
            self.attackJ()
            # self.attackJX()

    def attackFixed(self, roomNum: int):
        print("(前一个)房间" + str(roomNum) + "固定打法")
        if self.user == "NM":
            self.NMFixed(roomNum)
        if self.user == "GQ":
            self.GQFixed(roomNum)

    def getSkillXY(self, skillNum: int):
        if self.user == 'NM':
            skill = self.skillNM
        elif self.user == 'GQ':
            skill = self.skillGQ
        else:
            raise ValueError("无法识别当前人物类型")

        x, y = (self.windowsInfo[0] + (self.windowsInfo[2] * skill[skillNum][0]),
                self.windowsInfo[1] + (self.windowsInfo[3] * skill[skillNum][1]))
        self.adb.tap(x, y)
        self.adb.tap(x, y)
        return x, y

    def addBuff(self, t: float = 0.01):
        x, y = (self.windowsInfo[0] + (self.windowsInfo[2] * self.skillBuff[0][0]),
                self.windowsInfo[1] + (self.windowsInfo[3] * self.skillBuff[0][1]))
        self.adb.touch_start(x, y)
        self.adb.touch_move(x, y - 35)
        self.adb.touch_end(x, y)

    def addBuff2(self, t: float = 0.01):
        x, y = (self.windowsInfo[0] + (self.windowsInfo[2] * self.skillBuff[0][0]),
                self.windowsInfo[1] + (self.windowsInfo[3] * self.skillBuff[0][1]))
        self.adb.touch_start(x, y)
        self.adb.touch_move(x, y + 35)
        self.adb.touch_end(x, y)

    def clickAgain(self):
        x, y = (self.windowsInfo[0] + (self.windowsInfo[2] * 0.86),
                self.windowsInfo[1] + (self.windowsInfo[3] * 0.25))
        self.adb.tap(x, y)
        self.adb.tap(x, y)

    def getItemHeight(self):
        return self.windowsInfo[3] * 0.07

    def clickMap(self):
        x, y = (self.windowsInfo[0] + (self.windowsInfo[2] * 0.90),
                self.windowsInfo[1] + (self.windowsInfo[3] * 0.186))
        self.adb.tap(x, y)

    def getMapXY(self):
        return [(self.windowsInfo[2] * 0.380),  (self.windowsInfo[3] * 0.380),
                (self.windowsInfo[2] * 0.629),  (self.windowsInfo[3] * 0.637)]

    def get_window_xy(self):
        try:
            window = gw.getWindowsWithTitle(self.window_title)[0]
            if window:
                window.restore()
                window.activate()
                time.sleep(0.5)  # 等待窗口完全激活

                x, y, width, height = window.left, window.top, window.width, window.height
                self.windowsInfo = (x, y, width, height)

        except Exception as e:
            print(f"未找到窗口: {e}")

    def NMFixed(self, roomNum: int):
        if roomNum == 0:
            self.getSkillXY(5)
            self.getSkillXY(7)
        elif roomNum == 7:
            self.move(0, 0.1)
            self.getSkillXY(2)
            self.getSkillXY(6)
            self.move(270, 0.5)
            time.sleep(2)
            self.getSkillXY(4)
            time.sleep(0.3)
        elif roomNum == 13:
            time.sleep(1)
            self.getSkillXY(2)
            self.getSkillXY(6)
            time.sleep(0.5)
        elif roomNum == 14:
            self.getSkillXY(5)
            self.getSkillXY(0)
            time.sleep(0.5)
        elif roomNum == 15:
            self.move(90, 0.3)
            self.getSkillXY(4)
            time.sleep(1)
        elif roomNum == 9:
            print("狮子房间使用觉醒")
        elif roomNum == 8:
            self.getSkillXY(2)
            self.getSkillXY(1)
            self.getSkillXY(3)
            time.sleep(1)
        elif roomNum == 10:
            self.getSkillXY(2)
            self.getSkillXY(1)
            time.sleep(2)
        elif roomNum == 11:
            print("进入boss")
            self.getSkillXY(5)
            self.getSkillXY(0)
            time.sleep(5)

     # 0鬼影闪、1四阵、2鬼影剑、3鬼影鞭、4冥炎三、5鬼斩、6鬼月绝、7墓碑
    def GQFixed(self, roomNum: int):
        if roomNum == 0:
            self.addBuff2()
            self.getSkillXY(0)
            time.sleep(0.5)
        elif roomNum == 7:
            self.getSkillXY(2)
            self.move(0, 0.1)
            self.getSkillXY(7)
            self.getSkillXY(3)
            self.move(0, 0.2)
            time.sleep(2)
            self.getSkillXY(1)
            self.getSkillXY(1)
            time.sleep(0.3)
        elif roomNum == 13:
            time.sleep(1)
            self.getSkillXY(2)
            self.getSkillXY(3)
            time.sleep(0.5)
        elif roomNum == 14:
            self.getSkillXY(1)
            self.getSkillXY(1)
            self.getSkillXY(3)
            time.sleep(2)
        elif roomNum == 15:
            self.move(90, 0.3)
            self.getSkillXY(7)
            time.sleep(1)
        elif roomNum == 9:
            print("狮子房间使用觉醒")
        elif roomNum == 8:
            self.move(0, 0.2)
            self.getSkillXY(0)
            self.getSkillXY(7)
            time.sleep(1)
        elif roomNum == 10:
            time.sleep(1)
            self.getSkillXY(2)
            self.getSkillXY(3)
            time.sleep(2)
        elif roomNum == 11:
            print("进入boss")
            self.move(0, 0.4)
            self.getSkillXY(4)
            self.getSkillXY(7)
            time.sleep(5)


if __name__ == '__main__':
    window_title = "Phone-f0d62d51"
    ctl = GameControl(scrcpyQt(window_title), window_title)
    ctl.get_window_xy()

    ctl.attackFixed(1)
    # ctl.move(180, 1)  # 左
    # ctl.move(0, 1)  # 右
    # ctl.move(90, 1)  # 上
    # ctl.move(270, 1)  # 下

    # ctl.attack()
    # time.sleep(0.3)
    # ctl.move(270, 5)
    # time.sleep(0.3)
    # ctl.attack(3)
