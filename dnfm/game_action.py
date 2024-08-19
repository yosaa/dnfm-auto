from typing import Tuple, List, Optional
import math
import time
import cv2 as cv
import numpy as np
from .yolov5 import YoloV5s
from .game_control import GameControl
from .scrcpy_adb_qt import scrcpyQt
import random
from ncnn.utils.objects import Detect_Object

def get_object_bottom(obj: Detect_Object) -> Tuple[int, int]:
    return int(obj.rect.x + obj.rect.w / 2), int(obj.rect.y + obj.rect.h)

def compute_distance(a: Detect_Object, b: Detect_Object) -> float:
    return math.sqrt((a.rect.x - b.rect.x) ** 2 + (a.rect.y - b.rect.y) ** 2)

def calculate_angle(x1: int, y1: int, x2: int, y2: int) -> int:
    angle = math.atan2(y1 - y2, x1 - x2)
    return 180 - int(angle * 180 / math.pi)

def match_template(main_image: np.ndarray, sub_image: np.ndarray) -> bool:
    if main_image is None or sub_image is None:
        print("Error: 图片加载失败，请检查路径是否正确")
        return False

    sift = cv.SIFT_create()
    keypoints1, descriptors1 = sift.detectAndCompute(main_image, None)
    keypoints2, descriptors2 = sift.detectAndCompute(sub_image, None)

    if len(keypoints1) < 10 or len(keypoints2) < 10:
        print("Error: 特征点数量太少，无法进行匹配")
        return False

    flann = cv.FlannBasedMatcher()
    matches = flann.knnMatch(descriptors1, descriptors2, k=2)
    good_matches = [m for m, n in matches if m.distance < 0.7 * n.distance]
    # print(good_matches)
    return len(good_matches) > 10

def find_blue_color(image: np.ndarray) -> Tuple[int, int]:
    hsv_image = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    hue_opencv = int(211.72 / 2)
    saturation_opencv = int(94.98 * 255 / 100)
    value_opencv = int(93.73 * 255 / 100)

    lower_blue = np.array([hue_opencv - 10, saturation_opencv - 15, value_opencv - 15])
    upper_blue = np.array([hue_opencv + 10, saturation_opencv + 15, value_opencv + 15])
    mask = cv.inRange(hsv_image, lower_blue, upper_blue)
    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    if contours:
        x, y, w, h = cv.boundingRect(contours[0])
        return x + w // 2, y + h // 2
    else:
        print("未找到蓝色区域")
        return 0, 0

class GameAction:
    def __init__(self, ctrl: GameControl):
        self.speed_ratio = 0.17
        self.ctrl = ctrl
        self.yolo = YoloV5s(target_size=640, prob_threshold=0.25, nms_threshold=0.45, num_threads=4, use_gpu=True)
        self.adb = self.ctrl.adb
        self.moves = [self.ctrl.moveLU, self.ctrl.moveRD]
        # self.templates = [cv.imread(f'dnfm\\img\\SZT_{status}.png', cv.IMREAD_GRAYSCALE) for status in ['no', 'yes', 'ing']]
        # self.template_names = ['SZT_no', 'SZT_yes', 'SZT_ing']
        self.AGAIN = cv.imread('./dnfm/img/again.png')
        self.itemY = self.ctrl.get_item_height()
        self.true_count = 0
        self.next_room = False
        self.roomNum = 0
        self.unSZT = True

    def start(self):
        t = time.time()
        noHeroCount = 0
        fake_random = True
        keep_running = True

        while keep_running:
            time.sleep(0.1)
            screen = cv.cvtColor(np.array(self.ctrl.adb.on_frame()), cv.COLOR_RGB2BGR)
            if screen is None:
                continue

            AGAIN = match_template(self.AGAIN, screen)
            result = self.yolo(screen)
            self.draw_detections(screen, result)

            hero, monster, item, arrow, gate = self.categorize_objects(result)
            self.monster = monster
            self.arrow = arrow
            if not hero:
                noHeroCount += 1
                if len(monster) >= 4:
                    print(f"未找到英雄，但是当前怪物数量：{len(monster)} 尝试进行攻击")
                    self.fixed_attack()
                    continue
                if noHeroCount > 3:
                    print('随机移动')
                    self.moves[int(fake_random)]()
                    fake_random = not fake_random
                continue

            noHeroCount = 0
            hero = hero[0]
            hx, hy = get_object_bottom(hero)
            cv.circle(screen, (hx, hy), 5, (0, 0, 125), 5)

            min_distance_obj, action_type = self.determine_action(hero, monster, item, arrow, gate, AGAIN)

            if min_distance_obj:
                ax, ay = get_object_bottom(min_distance_obj)
                cv.circle(screen, (hx, hy), 5, (0, 255, 0), 5)
                cv.arrowedLine(screen, (hx, hy), (ax, ay), (255, 0, 0), 3)
                move_t = self.calculate_time(ax, ay, hx, hy)
                angle = calculate_angle(hx, hy, ax, ay + (self.itemY if action_type == 'item' else 0))
                sx, sy = self.ctrl.calc_mov_point(angle)
                self.perform_action(action_type, move_t, sx, sy)

            cv.imshow('screen', screen)
            if cv.waitKey(1) & 0xFF == ord('q'):
                keep_running = False

    def draw_detections(self, screen: np.ndarray, result: List[Detect_Object]):
        for obj in result:
            color = (0, 255, 0) if obj.label == 1 else (255, 0, 0) if obj.label == 5 else (0, 0, 255)
            cv.rectangle(screen, (int(obj.rect.x), int(obj.rect.y)), 
                         (int(obj.rect.x + obj.rect.w), int(obj.rect.y + obj.rect.h)), color, 2)
        cv.imshow('ada_image', screen)
        cv.waitKey(1)

    def categorize_objects(self, result: List[Detect_Object]) -> Tuple[List[Detect_Object], List[Detect_Object], List[Detect_Object], List[Detect_Object], List[Detect_Object]]:
        hero = [x for x in result if x.label == 1]
        monster = [x for x in result if x.label == 4]
        item = [x for x in result if x.label == 2]
        arrow = [x for x in result if x.label == 3]
        gate = [x for x in result if x.label == 0]
        return hero, monster, item, arrow, gate

    def determine_action(self, hero: Detect_Object, monster: List[Detect_Object], item: List[Detect_Object], arrow: List[Detect_Object], gate: List[Detect_Object], AGAIN: bool) -> Tuple[Optional[Detect_Object], str]:
        min_distance_obj = None
        action_type = ''

        if monster:
            print(f"发现怪物: {len(monster)}")
            if self.fixed_attack():
                return None, ''
            min_distance_obj = min(monster, key=lambda a: compute_distance(hero, a))
            action_type = 'attack'

        elif item:
            print(f"拾取物品：{len(item)}")
            min_distance_obj = min(item, key=lambda a: compute_distance(hero, a))
            action_type = 'item'

        elif arrow:
            if not self.next_room:
                self.next_room = True
                self.roomNum = self.judge_room_num()
                if self.roomNum in [8, 9] and self.unSZT:
                    self.move_to_SZT(self.roomNum)
                    return None, ''
            min_distance_obj = min(arrow, key=lambda a: compute_distance(hero, a))
            action_type = 'move'

        elif gate:
            print("发现门")
            min_distance_obj = min(gate, key=lambda a: compute_distance(hero, a))
            action_type = 'move'

        elif AGAIN:
            self.handle_again_scenario()
            return None, ''

        else:
            print("未识别到任何物体, 随机移动")
            self.moves[int(random.random() > 0.5)]()
            return None, ''

        return min_distance_obj, action_type

    def calculate_time(self, ax: int, ay: int, hx: int, hy: int) -> float:
        distance = math.sqrt((hx - ax) ** 2 + (hy - ay) ** 2)
        return distance / 497

    def fixed_attack(self) -> bool:
        if self.next_room:
            self.ctrl.attack_fixed(self.roomNum)
            self.next_room = False
            return True
        return False

    def judge_room_num(self) -> Optional[int]:
        self.ctrl.click_map()
        time.sleep(0.1)
        screen_map = cv.cvtColor(np.array(self.ctrl.adb.on_frame()), cv.COLOR_RGB2BGR)
        room_num = self.get_user_position(screen_map)
        self.ctrl.click_map()
        print(f"当前房间号: {room_num}")
        return room_num

    def move_to_SZT(self, roomNum: int):
        print("识别到狮子头")
        fail_times = 0
        while roomNum != 8:
            fail_times += 1
            if fail_times >= 2:
                self.ctrl.move(0, 0.2)
                self.ctrl.move(270, 0.2)
                self.ctrl.move(180, 0.1)
                roomNum = self.judge_room_num()
            self.ctrl.move(180, 2)
            self.ctrl.move(0, 0.3)
            self.ctrl.move(90, 0.3)
            self.ctrl.move(180, 1)
            roomNum = self.judge_room_num()
        self.ctrl.attackJX()

    def get_user_position(self, image: np.ndarray) -> Optional[int]:
        x1, y1, x2, y2 = map(int, self.ctrl.get_map_xy())
        cropped_image = image[y1:y2, x1:x2]
        height, width, _ = cropped_image.shape

        num_rows, num_cols = 3, 6
        cell_width, cell_height = width // num_cols, height // num_rows
        region_ranges = [(c * cell_width, r * cell_height, (c + 1) * cell_width, (r + 1) * cell_height) for r in range(num_rows) for c in range(num_cols)]

        blue_x, blue_y = find_blue_color(cropped_image)
        for r, (left, top, right, bottom) in enumerate(region_ranges):
            if left <= blue_x <= right and top <= blue_y <= bottom:
                return r * num_cols + region_ranges.index((left, top, right, bottom)) + 1
        return None

    def handle_again_scenario(self):
        global again_times
        if again_times == 2:
            self.unSZT = True
            print("开始下一局")
            self.ctrl.click_again()
            time.sleep(4)
            again_times = 0
            self.roomNum = 0
        elif again_times == 0:
            print("准备开始下一局，看看右边有什么没捡的")
            self.moves[1]()
            again_times += 1
        else:
            print("准备开始下一局，看看左边有什么没捡的")
            self.moves[0]()
            self.moves[0]()
            again_times += 1

    def perform_action(self, action_type: str, move_t: float, sx: int, sy: int):
        if action_type == 'attack':
            self.adb.tap(sx, sy, move_t * 0.7)
            print("攻击怪物")
            self.ctrl.attack_combine(len(self.monster))
        elif action_type == 'item':
            self.adb.tap(sx, sy, move_t)
        elif action_type == 'move':
            self.adb.tap(sx, sy, 2 if len(self.arrow) > 3 else move_t)

if __name__ == '__main__':
    window_title = "Phone-f0d62d51"
    ctrl = GameControl(scrcpyQt(window_title), window_title)
    action = GameAction(ctrl)

    while True:
        action.start()
        time.sleep(3)
