from typing import Tuple

from yolov5 import YoloV5s
from game_control import GameControl
from scrcpy_adb_qt import scrcpyQt
import time
import cv2 as cv
from ncnn.utils.objects import Detect_Object
import math
import numpy as np
import random


def get_detect_obj_bottom(obj: Detect_Object) -> Tuple[int, int]:
    return int(obj.rect.x + obj.rect.w / 2), int(obj.rect.y + obj.rect.h)


def distance_detect_object(a: Detect_Object, b: Detect_Object):
    return math.sqrt((a.rect.x - b.rect.x) ** 2 + (a.rect.y - b.rect.y) ** 2)


def calc_angle(x1, y1, x2, y2):
    angle = math.atan2(y1 - y2, x1 - x2)
    return 180 - int(angle * 180 / math.pi)


class GameAction:
    def __init__(self, ctrl: GameControl):
        self.ctrl = ctrl
        self.yolo = YoloV5s(target_size=640,
                            prob_threshold=0.25,
                            nms_threshold=0.45,
                            num_threads=4,
                            use_gpu=True)
        self.adb = self.ctrl.adb
        self.moves = [
            lambda: self.ctrl.moveLU(),
            lambda: self.ctrl.moveRD()
        ]
        self.SZT_no = cv.imread('dnfm\\img\\SZT_no.png', cv.IMREAD_GRAYSCALE)
        self.SZT_yes = cv.imread('dnfm\\img\\SZT_yes.png', cv.IMREAD_GRAYSCALE)
        self.SZT_ing = cv.imread('dnfm\\img\\SZT_ing.png', cv.IMREAD_GRAYSCALE)

        self.templates = [self.SZT_no, self.SZT_yes, self.SZT_ing]
        self.template_names = ['SZT_no', 'SZT_yes', 'SZT_ing']
        self.AGAIN = cv.imread('dnfm\\img\\again.png')
        self.itemY = self.ctrl.getItemHeight()
        self.true_count = 0
        self.next_room = False
        self.roomNum = 0

    def mov_to_next_room(self):
        t = time.time()
        mov_start = False
        noHeroCount = 0
        keep_running = True
        fake_random = True
        again_times = 0
        unBuff = True
        self.unSZT = True
        thisTimeIsItems = False

        while keep_running:
            time.sleep(0.1)
            screen_row = self.ctrl.adb.on_frame()
            screen = cv.cvtColor(np.array(screen_row), cv.COLOR_RGB2BGR)
            if screen is None:
                continue

            AGAIN = match_template(self.AGAIN, screen)
            # ada_image = cv.adaptiveThreshold(cv.cvtColor(
            #     screen, cv.COLOR_BGR2GRAY), 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 13, 3)
            # cv.imshow('ada_image', ada_image)
            # cv.waitKey(1)
            # if np.sum(ada_image) == 0:
            #     print('过图成功')
            #     self.adb.touch_end(0, 0)
            #     return

            result = self.yolo(screen)
            # for obj in result:
            #     color = (0, 255, 0)
            #     if obj.label == 1:
            #         color = (255, 0, 0)
            #     elif obj.label == 5:
            #         color = (0, 0, 255)
            #     cv.rectangle(screen,
            #                  (int(obj.rect.x), int(obj.rect.y)),
            #                  (int(obj.rect.x + obj.rect.w),
            #                   int(obj.rect.y + + obj.rect.h)),
            #                  color, 2
            #                  )

            hero = [x for x in result if x.label == 1]
            monster = [x for x in result if x.label == 4]
            if len(hero) == 0:
                print('没有找到英雄')
                noHeroCount += 1
                hero = None
                if (len(monster) >= 4):
                    mov_start = False
                    print("未找到英雄，但是当前怪物数量：" + str(len(monster)) + "尝试进行攻击")
                    self.fixedAttack()
                    # self.ctrl.attackCombine(len(monster))
                elif (noHeroCount > 3):
                    noHeroCount = 0
                    print('随机移动')
                    index = 0 if fake_random else 1
                    self.moves[index]()
                    fake_random = not fake_random
                continue
            else:
                if unBuff:
                    self.ctrl.addBuff()
                    unBuff = False
                    self.roomNum = self.judge_room_num()
                    if self.roomNum == 7:
                        self.ctrl.attackFixed(0)
                hero = hero[0]
                hx, hy = get_detect_obj_bottom(hero)
                cv.circle(screen, (hx, hy), 5, (0, 0, 125), 5)
                noHeroCount = 0

            item = [x for x in result if x.label == 2]
            arrow = [x for x in result if x.label == 3]
            gate = [x for x in result if x.label == 0]
            if len(monster) != 0:
                mov_start = False
                print("发现怪物: " + str(len(monster)))
                fixedAttack = self.fixedAttack()
                if fixedAttack == True:
                    continue
                min_distance_arrow = min(
                    monster, key=lambda a: distance_detect_object(hero, a))
            elif len(item) != 0:
                print("拾取物品：" + str(len(item)))
                thisTimeIsItems = True
                min_distance_arrow = min(
                    item, key=lambda a: distance_detect_object(hero, a))
            elif len(arrow) != 0:
                if not mov_start:
                    self.next_room = True
                    self.roomNum = self.judge_room_num()
                    if self.roomNum == 9 and self.unSZT:
                        # 移动到狮子头位置
                        self.move_to_SZT(self.roomNum)
                        continue
                    elif self.roomNum == 10:
                        self.unSZT = False
                print("开始寻路")
                min_distance_arrow = min(
                    arrow, key=lambda a: distance_detect_object(hero, a))
                # 标志可能在脚下
                if len(arrow) >= 2:
                    min_distance_arrow_second = min(
                        (a for a in arrow if a != min_distance_arrow),
                        key=lambda a: distance_detect_object(hero, a))
                    min_distance_arrow = min_distance_arrow_second
            elif len(gate) != 0:
                print("发现门")
                min_distance_arrow = min(
                    gate, key=lambda a: distance_detect_object(hero, a))
            elif AGAIN:
                if again_times == 2:
                    unBuff = True
                    self.unSZT = True
                    print("开始下一局")
                    self.ctrl.clickAgain()
                    time.sleep(4)
                    again_times = 0
                    self.roomNum = 0
                elif again_times == 0:
                    print("准备开始下一局，看看右边有什么没捡的")
                    self.moves[1]()
                    self.moves[1]()
                    again_times += 1
                else:
                    print("准备开始下一局，看看左边有什么没捡的")
                    self.moves[1]()
                    self.moves[0]()
                    self.moves[0]()
                    again_times += 1
                continue
            else:
                print("未识别到任何物体,随机移动")
                index = 0 if fake_random else 1
                self.moves[index]()
                fake_random = not fake_random
                continue

            ax, ay = get_detect_obj_bottom(min_distance_arrow)
            # cv.circle(screen, (hx, hy), 5, (0, 255, 0), 5)
            # cv.arrowedLine(screen, (hx, hy), (ax, ay), (255, 0, 0), 3)

            if thisTimeIsItems:
                angle = calc_angle(hx, hy, ax, (ay + self.itemY))
                thisTimeIsItems = False
            else:
                angle = calc_angle(hx, hy, ax, ay)
            sx, sy = self.ctrl.calc_mov_point(angle)

            if len(monster) != 0:
                self.adb.tap(sx, sy, 0.1)
                print("攻击怪物")
                self.ctrl.attackCombine(len(monster))

            elif len(item) != 0:
                self.adb.tap(sx, sy, 0.3)
            elif not mov_start:
                self.adb.tap(sx, sy, 0.2)
                mov_start = True
            else:
                self.adb.tap(sx, sy, 1)

            # cv.imshow('screen', screen)
            # cv.waitKey(2)
            # 检查是否按下 'q' 键退出程序
            if cv.waitKey(1) & 0xFF == ord('q'):
                keep_running = False

    def fixedAttack(self):
        if self.next_room:
            self.ctrl.attackFixed(self.roomNum)
            self.next_room = False
            return True
        else:
            return False

    def judge_room_num(self):
        # 判断房间号
        self.ctrl.clickMap()
        time.sleep(0.1)
        screen_map = self.ctrl.adb.on_frame()
        screen_map = cv.cvtColor(
            np.array(screen_map), cv.COLOR_RGB2BGR)
        roomNum = self.getUserPosition(screen_map)
        self.ctrl.clickMap()
        print("当前房间号:" + str(roomNum))
        return roomNum

    def move_to_SZT(self, roomNum):
        print("识别到狮子头")
        while roomNum != 8:
            self.ctrl.move(180, 2)
            self.ctrl.move(0, 0.3)
            self.ctrl.move(90, 0.5)
            self.ctrl.move(180, 1)
            self.ctrl.move(0, 0.1)
            self.ctrl.move(270, 0.5)
            roomNum = self.judge_room_num()

        self.ctrl.attackJX()

    def getUserPosition(self, image):
        x1, y1, x2, y2 = map(int, self.ctrl.getMapXY())
        # 裁剪图像
        cropped_image = image[y1:y2, x1:x2]
        # 获取裁剪图像的宽度和高度
        height, width, _ = cropped_image.shape
        # cv.imshow('Blue Region', cropped_image)
        # cv.waitKey(2)
        # 将图像分成3x3的网格
        num_rows = 3
        num_cols = 6
        cell_width = width // num_cols
        cell_height = height // num_rows

        # 计算每个区域的范围，并存储在二维数组中
        region_ranges = []
        for r in range(num_rows):
            row_ranges = []
            for c in range(num_cols):
                # 计算当前区域的范围
                left = c * cell_width
                right = left + cell_width
                top = r * cell_height
                bottom = top + cell_height
                region = (left, top, right, bottom)
                row_ranges.append(region)
            region_ranges.append(row_ranges)

        # 假设已经通过其他方法找到了蓝色点的坐标 blue_x, blue_y
        blue_x, blue_y = find_blue_color(cropped_image)
        for r in range(num_rows):
            for c in range(num_cols):
                left, top, right, bottom = region_ranges[r][c]
                if left <= blue_x <= right and top <= blue_y <= bottom:
                    # 找到了蓝色点所在的区域
                    region_number = r * num_cols + c + 1  # 区域编号从1开始
                    return region_number
        # 如果未找到匹配的区域，返回默认值或者错误处理
        return None


def find_blue_color(image):
    # 将图像转换为HSV颜色空间
    hsv_image = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    # 定义蓝色的HSV颜色范围
    hue_degree = 211.72
    saturation_percent = 94.98
    value_percent = 93.73

    # 转换为OpenCV中的HSV范围
    hue_opencv = int(hue_degree / 2)
    saturation_opencv = int(saturation_percent * 255 / 100)
    value_opencv = int(value_percent * 255 / 100)

    # 定义颜色范围
    lower_blue = np.array(
        [hue_opencv - 10, saturation_opencv - 15, value_opencv - 15])
    upper_blue = np.array(
        [hue_opencv + 10, saturation_opencv + 15, value_opencv + 15])

    # 创建蓝色区域的掩膜
    mask = cv.inRange(hsv_image, lower_blue, upper_blue)

    # 找到蓝色区域的轮廓
    contours, _ = cv.findContours(
        mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    # 如果找到了轮廓
    if contours:
        # 计算蓝色区域的最小包围矩形
        x, y, w, h = cv.boundingRect(contours[0])

        # 计算蓝色区域的中心点
        blue_x = x + w // 2
        blue_y = y + h // 2
        return blue_x, blue_y
    else:
        print("未找到蓝色区域")
        return 0, 0


def match_template(main_image, sub_image):
    # 检查图片是否正确加载
    if main_image is None or sub_image is None:
        print("Error: 图片加载失败，请检查路径是否正确")
        return False

    # 使用SIFT算法提取特征点
    sift = cv.SIFT_create(nfeatures=0)
    keypoints1, descriptors1 = sift.detectAndCompute(main_image, None)
    keypoints2, descriptors2 = sift.detectAndCompute(sub_image, None)

    # 如果特征点数量太少，则认为匹配失败
    if len(keypoints1) < 10 or len(keypoints2) < 10:
        print("Error: 特征点数量太少，无法进行匹配")
        return False

    # 使用FLANN匹配器进行特征匹配
    flann = cv.FlannBasedMatcher()
    matches = flann.knnMatch(descriptors1, descriptors2, k=2)

    good_matches = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good_matches.append(m)

    MIN_MATCH_COUNT = 10
    if len(good_matches) > MIN_MATCH_COUNT:
        return True
    else:
        return False


if __name__ == '__main__':
    window_title = "Phone-f0d62d51"
    ctrl = GameControl(scrcpyQt(window_title), window_title)
    action = GameAction(ctrl)

    while True:
        action.mov_to_next_room()
        time.sleep(3)
