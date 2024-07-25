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

    def mov_to_next_room(self):
        t = time.time()
        mov_start = False
        noHeroCount = 0
        keep_running = True
        fake_random = True
        again_times = 0
        nextRound = True
        thisTimeIsItems = False

        while keep_running:
            time.sleep(0.1)
            screen_row = self.ctrl.adb.on_frame()
            screen = cv.cvtColor(np.array(screen_row), cv.COLOR_RGB2BGR)
            if screen is None:
                continue
            SZT = self.find_best_match(screen)
            print(SZT)
            # AGAIN = match_template(self.AGAIN, screen)
            continue
            ada_image = cv.adaptiveThreshold(cv.cvtColor(
                screen, cv.COLOR_BGR2GRAY), 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 13, 3)
            # cv.imshow('ada_image', ada_image)
            # cv.waitKey(1)
            if np.sum(ada_image) == 0:
                print('过图成功')
                self.adb.touch_end(0, 0)
                return

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
                    print("未找到英雄，但是当前怪物数量：" + str(len(monster)) + "尝试进行攻击")
                    self.ctrl.attackY()
                    self.ctrl.attackY()
                    # self.ctrl.attackCombine(len(monster))
                elif (noHeroCount > 3):
                    noHeroCount = 0
                    print('随机移动')
                    index = 0 if fake_random else 1
                    self.moves[index]()
                    fake_random = not fake_random
                continue
            else:
                if nextRound:
                    self.ctrl.addBuff()
                    nextRound = False
                hero = hero[0]
                hx, hy = get_detect_obj_bottom(hero)
                cv.circle(screen, (hx, hy), 5, (0, 0, 125), 5)
                noHeroCount = 0

            item = [x for x in result if x.label == 2]
            arrow = [x for x in result if x.label == 3]
            gate = [x for x in result if x.label == 0]
            if len(monster) != 0 and SZT:
                print("进入狮子头前一个房间: ")
                sztx, szty = self.ctrl.getCenterXY()
                angle = calc_angle(hx, hy, sztx, szty)
                self.ctrl.move(angle, 0.3)
                self.ctrl.attackJ()
                self.ctrl.attack()
                self.ctrl.move(0, 1)
                continue
            elif len(monster) != 0:
                print("发现怪物: " + str(len(monster)))
                min_distance_arrow = min(
                    monster, key=lambda a: distance_detect_object(hero, a))
            elif SZT:
                print("识别到狮子头")
                sztx, szty = self.ctrl.getCenterXY()
                angle = calc_angle(hx, hy, sztx, szty)
                self.ctrl.move(angle, 0.2)
                self.ctrl.move(angle, 0.3)
                self.ctrl.move(180, 2)
                continue
            elif len(item) != 0:
                print("拾取物品：" + str(len(item)))
                thisTimeIsItems = True
                min_distance_arrow = min(
                    item, key=lambda a: distance_detect_object(hero, a))
            elif len(arrow) != 0:
                print("开始寻路")
                min_distance_arrow = min(
                    arrow, key=lambda a: distance_detect_object(hero, a))
            elif len(gate) != 0:
                print("发现门")
                min_distance_arrow = min(
                    gate, key=lambda a: distance_detect_object(hero, a))
            elif AGAIN:
                if again_times == 3:
                    nextRound = True
                    print("开始下一局")
                    time.sleep(2)
                elif again_times == 0:
                    self.moves[1]()
                    self.moves[1]()
                else:
                    self.moves[1]()
                    self.moves[0]()
                    self.moves[0]()
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
            # cv.waitKey(1)
            # 检查是否按下 'q' 键退出程序
            if cv.waitKey(1) & 0xFF == ord('q'):
                keep_running = False

    def find_best_match(self, image):
        self.ctrl.getMapXY()
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        # 裁剪图像
        cropped_image = image[y1:y2, x1:x2]
        # 将输入图像转换为灰度图像
        gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)



        best_match_name = 'SZT_yes'  # 默认值
        best_match_score = 0.7  # 以比例表示的阈值

        for template, name in zip(self.templates, self.template_names):
            # result = cv.matchTemplate(gray_image, template, cv.TM_CCOEFF_NORMED)
            result = match_template(template, gray_image)
            _, max_val, _, _ = cv.minMaxLoc(result)
            print(max_val)
            if max_val > best_match_score:
                best_match_score = max_val
                best_match_name = name

        return best_match_name

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

    MIN_MATCH_COUNT = 20
    return len(good_matches)
    # if len(good_matches) > MIN_MATCH_COUNT:
    #     return True
    # else:
    #     return False



if __name__ == '__main__':
    window_title = "Phone-f0d62d51"
    ctrl = GameControl(scrcpyQt(window_title), window_title)
    action = GameAction(ctrl)

    while True:
        action.mov_to_next_room()
        time.sleep(3)
