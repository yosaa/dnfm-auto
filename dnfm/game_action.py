from typing import Tuple, List, Optional
import math
import time
import threading
import cv2 as cv
import numpy as np
from .yolov5 import YoloV5s
from .game_control import GameControl
from .scrcpy_adb_qt import ScrcpyADB
import random
from ncnn.utils.objects import Detect_Object
from dnfm.utils.cvmatch import image_match_util


def get_object_bottom(obj: Detect_Object) -> Tuple[int, int]:
    return int(obj.rect.x + obj.rect.w / 2), int(obj.rect.y + obj.rect.h)


def compute_distance(a: Detect_Object, b: Detect_Object) -> float:
    return math.sqrt((a.rect.x - b.rect.x) ** 2 + (a.rect.y - b.rect.y) ** 2)


def calculate_angle(x1: int, y1: int, x2: int, y2: int) -> int:
    angle = math.atan2(y1 - y2, x1 - x2)
    return 180 - int(angle * 180 / math.pi)


def find_blue_color(image: np.ndarray) -> Tuple[int, int]:
    hsv_image = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    hue_opencv = int(211.72 / 2)
    saturation_opencv = int(94.98 * 255 / 100)
    value_opencv = int(93.73 * 255 / 100)

    lower_blue = np.array(
        [hue_opencv - 10, saturation_opencv - 15, value_opencv - 15])
    upper_blue = np.array(
        [hue_opencv + 10, saturation_opencv + 15, value_opencv + 15])
    mask = cv.inRange(hsv_image, lower_blue, upper_blue)
    contours, _ = cv.findContours(
        mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

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
        self.yolo = YoloV5s(target_size=640, prob_threshold=0.25,
                            nms_threshold=0.45, num_threads=4, use_gpu=False)
        self.adb = self.ctrl.adb
        self.moves = [self.ctrl.moveLU, self.ctrl.moveRD]
        # self.templates = [cv.imread(f'dnfm\\img\\SZT_{status}.png', cv.IMREAD_GRAYSCALE) for status in ['no', 'yes', 'ing']]
        # self.template_names = ['SZT_no', 'SZT_yes', 'SZT_ing']
        self.AGAIN = cv.imread('template/again/again.png')
        self.BACK = cv.imread('template/weituo/back.png')
        self.CONFIRM = cv.imread('template/weituo/qr.png')
        self.repairEquipment = cv.imread('template/repair_equipment.png')

        self.matchAgain = False
        self.itemY = self.ctrl.get_item_height()
        self.true_count = 0
        self.next_room = True
        self.roomNum = 0
        self.BWJRoom = [0, 7, 13, 14, 15, 9, 8, 9, 10, 11, 12]
        self.unSZT = True
        self.result = None
        self.next_angle = 0
        self.again_times = 0
        self.last_update_time = None
        self.last_judge_room_num_time = None
        self.calibration_room = False
        self.must_calibration_room = False
        self.entering = False
        self.item = None
        self.monster = None
        self.arrow = None

    def match_again(self):
        try:
            # 发现修理装备，就修理
            crop = (1914, 117, 361, 475)
            crop = tuple(int(value ) for value in crop)
            repair_res = image_match_util.match_template_best(self.repairEquipment, self.ctrl.adb.last_screen, crop)
            if repair_res is not None:
                print('发现修理装备按钮,点击修理装备')
                x, y, w, h = repair_res['rect']
                time.sleep(1)
                self.ctrl.click((x + w / 2) / self.ctrl.adb.zoom_ratio, (y + h / 2) / self.ctrl.adb.zoom_ratio)
                time.sleep(1)
                # 点击修理
                self.ctrl.click(1168, 963)
                time.sleep(1)
                self.ctrl.click(1168, 963)
                time.sleep(1)
                self.ctrl.click((x + w / 2) / self.ctrl.adb.zoom_ratio, (y + h / 2) / self.ctrl.adb.zoom_ratio)
                time.sleep(0.3)
            # 截取区域 xywh
            crop = (1914, 117, 361, 275)
            crop = tuple(int(value * 1) for value in crop)
            result = image_match_util.match_template_best(self.AGAIN, self.adb.last_screen, crop)
            if result:
                # 发现了再次挑战，就重开
                print('发现再次挑战按钮,点击重开')
                x, y, w, h = result['rect']
                time.sleep(0.8)
                self.ctrl.click((x + w / 2) / self.ctrl.adb.zoom_ratio, (y + h / 2) / self.ctrl.adb.zoom_ratio)
                
                time.sleep(1)
                clickConfirm = 0
                while clickConfirm < 3:
                    if self.match_confirm():
                       print('成功点击再次挑战按钮')
                       break
                    time.sleep(0.5)
                    clickConfirm += 1
                # self.ctrl.click(1345, 679)

                # 初始化变量
                self.unSZT = True
                self.again_times = 0
                self.roomNum = 0
                self.next_room = True
                self.matchAgain = False
                return True
        except Exception as e:
            print('没有找到再次挑战按钮:', e)
            return False
        # return False


    def find_result(self):
        while True:
            time.sleep(0.01)
            screen = self.ctrl.adb.last_screen
            if screen is None:
                continue
            s = time.time()
            result = self.yolo(screen)
            print(f'匹配耗时{int((time.time() - s) * 1000)} ms')
            return screen, result
           
    def task(self):
        while True:
            time.sleep(0.2)
            screen = self.adb.last_screen
            if screen is None:
                continue

            ada_image = cv.adaptiveThreshold(cv.cvtColor(
                screen, cv.COLOR_BGR2GRAY), 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 13, 3)

            if np.sum(ada_image) < 500000:
                self.entering = False
                print('<<<<<<<-------------过图成功------------>>>>>>>')
                current_time = time.time()
                if self.last_update_time is None or current_time - self.last_update_time > 2:
                    if self.roomNum == 3:
                        index = 4
                    else:
                        index = self.BWJRoom.index(self.roomNum)
                        if index == 5 and self.unSZT is False:
                            index += 2
                    if index + 1 > len(self.BWJRoom):
                        self.must_calibration_room = True
                    else:
                        try:
                            self.roomNum = self.BWJRoom[index + 1]
                        except:
                            self.must_calibration_room = True
                    self.next_room = True
                    self.last_update_time = current_time
                    self.calibration_room = True
                self.adb.touch_end(0, 0)
            else:
                self.entering = False

            if self.roomNum in [0,  11, 12] and not self.item and not self.monster and not self.arrow:
                self.match_again()
                print("<<<<<<<<<<匹配到再次挑战>>>>>>>>>>>")

    def start_thread(self):
        thread = threading.Thread(target=self.task)
        thread.daemon = True  # 确保主线程退出时子线程也能退出
        thread.start()

    def start(self):
        noHeroCount = 0
        keep_running = True

        while keep_running:
            if self.entering:
                self.adb.touch_end(0, 0)
                time.sleep(0.2)
                continue

            # screen = self.ctrl.adb.last_screen
            screen, result = self.find_result()
            if screen is None:
                continue

            if self.roomNum == 0 and self.next_room:
                if self.match_again():
                    continue
                self.roomNum = self.judge_room_num()
                if self.roomNum == 7:
                    self.fixed_attack()
                self.next_room = False
                
                continue
            judge_room_time = time.time()
            if self.must_calibration_room or (self.roomNum in [3, 9, 10, 15] and (self.calibration_room or (self.last_judge_room_num_time is None or judge_room_time - self.last_judge_room_num_time > 15))):
                self.roomNum = self.judge_room_num()
                self.calibration_room = False
                self.must_calibration_room = False
                self.last_judge_room_num_time = judge_room_time

            self.yolo_result = result
            # self.draw_detections(screen, self.yolo_result)
            hero, monster, item, arrow, gate = self.categorize_objects(
                self.yolo_result)
            self.monster = monster
            self.arrow = arrow
            self.item = item
            if not hero:
                noHeroCount += 1
                if len(monster) >= 4:
                    print(f"未找到英雄，但是当前怪物数量：{len(monster)} 尝试进行攻击")
                    self.ctrl.attack()
                    continue
                if noHeroCount > 3:
                    print('未找到英雄,随机移动')
                    # self.moves[int(fake_random)]()
                    # fake_random = not fake_random
                    self.no_hero_handle(None, 0.4)
                    self.ctrl.attack()

                continue

            noHeroCount = 0
            hero = hero[0]
            hx, hy = get_object_bottom(hero)
            cv.circle(screen, (hx, hy), 5, (0, 0, 125), 5)

            min_distance_obj, action_type = self.determine_action(
                hero, monster, item, arrow, gate, self.matchAgain)

            if min_distance_obj:
                ax, ay = get_object_bottom(min_distance_obj)
                cv.circle(screen, (hx, hy), 5, (0, 255, 0), 5)
                cv.arrowedLine(screen, (hx, hy), (ax, ay), (255, 0, 0), 3)
                move_t = self.calculate_time(ax, ay, hx, hy)
                angle = calculate_angle(
                    hx, hy, ax, ay + (self.itemY if action_type == 'item' else 0))
                sx, sy = self.ctrl.calc_mov_point(angle)
                self.perform_action(action_type, move_t,
                                    sx, sy, ax, ay, hx, hy)

            # cv.imshow('screen', screen)

    def draw_detections(self, screen: np.ndarray, result: List[Detect_Object]):
        print("关闭识别效果打印")
        # for obj in result:
        #     color = (2 ** (obj.label % 9) - 1, 2 ** ((obj.label + 4) %
        #              9) - 1, 2 ** ((obj.label + 8) % 9) - 1)
        #     text = f"{self.yolo.class_names[int(obj.label)]}:{obj.prob:.2f}"
        #     range_local = [obj.rect.x, obj.rect.y,
        #                    obj.rect.x + obj.rect.w, obj.rect.y + obj.rect.h]
        #     self.plot_one_box(range_local, screen,
        #                       color=color, label=text, line_thickness=2)
        # cv.imshow('ada_image', screen)
        # cv.waitKey(1)

    def plot_one_box(self, x, img_source, color=None, label=None, line_thickness=None):
        # 线条粗细
        tl = line_thickness or round(
            0.002 * (img_source.shape[0] + img_source.shape[1]) / 2) + 1
        color = color or [0, 255, 0]  # 默认绿色
        c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))  # 转换坐标为整数

        # 画框
        cv.rectangle(img_source, c1, c2, color,
                     thickness=tl, lineType=cv.LINE_AA)

        if label:
            tf = max(tl - 1, 2)  # 文本字体大小
            text_color = [255, 255, 255]  # 默认白色，可以考虑通过参数传递
            text_color = text_color if color is None else color  # 如果有颜色参数，则使用此颜色作为文字颜色

            # 在原位置绘制文本，无背景
            cv.putText(img_source, label, (c1[0], c1[1] - 2), 0, tl / 3, text_color, thickness=tf,
                       lineType=cv.LINE_AA)

    def categorize_objects(self, result: List[Detect_Object]) -> Tuple[List[Detect_Object], List[Detect_Object], List[Detect_Object], List[Detect_Object], List[Detect_Object]]:
        hero = [x for x in result if x.label == 1]
        monster = [x for x in result if x.label == 4]
        item = [x for x in result if x.label == 2]
        arrow = [x for x in result if x.label == 3]
        gate = [x for x in result if x.label == 0]
        # gate_szt = [x for x in result if x.label == 1]
        return hero, monster, item, arrow, gate

    def determine_action(self, hero: Detect_Object, monster: List[Detect_Object], item: List[Detect_Object], arrow: List[Detect_Object], gate: List[Detect_Object], AGAIN: bool) -> Tuple[Optional[Detect_Object], str]:
        min_distance_obj = None
        action_type = ''

        if monster:
            print(f"发现怪物: {len(monster)}")
            # if self.fixed_attack():
            #     return None, ''
            min_distance_obj = min(
                monster, key=lambda a: compute_distance(hero, a))
            action_type = 'attack'

        elif item:
            print(f"拾取物品：{len(item)}")
            min_distance_obj = min(
                item, key=lambda a: compute_distance(hero, a))
            action_type = 'item'

        elif arrow:
            if self.roomNum == 10 and self.unSZT:
                self.ctrl.move(180, 3)
                if self.judge_room_num() == 9:
                    self.ctrl.move(180, 3)
                    self.move_to_SZT()
                    return None, ''
            if self.roomNum == 9 and self.unSZT:
                self.move_to_SZT()
                return None, ''
            min_distance_obj = min(
                arrow, key=lambda a: compute_distance(hero, a))
            action_type = 'move'

        elif gate: 
            if self.roomNum == 9 and self.unSZT:
                self.move_to_SZT()
                return None, ''
            print("发现门")
            min_distance_obj = min(
                gate, key=lambda a: compute_distance(hero, a))
            action_type = 'goDoor'

        elif AGAIN:
            print("识别到再次挑战")
            return None, ''

        else:
            print("未识别到任何物体, 随机移动")
            self.no_hero_handle(None, 0.4)
            # self.moves[int(random.random() > 0.5)]()
            self.ctrl.attack()

            return None, ''

        return min_distance_obj, action_type

    def calculate_time(self, ax: int, ay: int, hx: int, hy: int) -> float:
        distance = math.sqrt((hx - ax) ** 2 + (hy - ay) ** 2)
        return distance / 520 / 2

    def fixed_attack(self) -> bool:
        if self.next_room:
            if self.roomNum == 8:
                self.roomNum == self.judge_room_num()
                if self.roomNum == 8:
                    self.unSZT = False

            if self.unSZT is False and self.roomNum == 9:
                print("已经打过该房间")
            else:
                self.ctrl.attack_fixed(self.roomNum)
            self.next_room = False
            return True
        return False

    def judge_room_num(self) -> Optional[int]:
        if self.matchAgain:
            return 12
        self.adb.touch_end(0, 0)
        time.sleep(0.2)
        self.ctrl.click_map()
        time.sleep(1)
        screen_map = self.ctrl.adb.last_screen
        room_num = self.get_user_position(screen_map)
        self.ctrl.click_map()
        print(f"当前房间号: {room_num}")
        if room_num == 8:
            self.unSZT = False
        return room_num

    def move_to_SZT(self):
        print("识别到狮子头")
        fail_times = 1
        while self.roomNum != 8:
            if fail_times % 2 == 0:
                time.sleep(0.2)
                self.ctrl.move(225, 0.4)
                time.sleep(0.1)
                self.ctrl.move(0, 0.2)
                self.ctrl.move(270, 0.2)
                fail_times += 1
                self.roomNum = self.judge_room_num()
            else:
                time.sleep(0.2)
                self.ctrl.move(165, 1)
                time.sleep(0.1)
                self.ctrl.move(0, 0.5)
                time.sleep(0.1)
                self.ctrl.move(90, 0.4)
                time.sleep(0.1)
                self.ctrl.move(150, 0.5)
                self.roomNum = self.judge_room_num()
                fail_times += 1
            if self.roomNum in [3, 10, 15]:
                print("进错房间了")
                if self.roomNum in [10, 15]:
                    self.next_room = False
                else:
                    self.ctrl.move(90, 1.5)
                    self.ctrl.attack()
                break
        if self.roomNum == 8:
            self.unSZT = False
            self.ctrl.attack_fixed(self.roomNum)

    def get_user_position(self, image: np.ndarray) -> Optional[int]:
        x1, y1, x2, y2 = map(int, self.ctrl.get_map_xy())
        cropped_image = image[y1:y2, x1:x2]
        height, width, _ = cropped_image.shape

        # 定义网格
        num_rows, num_cols = 3, 6
        cell_width, cell_height = width // num_cols, height // num_rows

        blue_x, blue_y = find_blue_color(cropped_image)
        # 遍历每个网格
        for r in range(num_rows):
            for c in range(num_cols):
                left = c * cell_width
                top = r * cell_height
                right = (c + 1) * cell_width
                bottom = (r + 1) * cell_height

                # 判断蓝点是否在当前网格内
                if left <= blue_x < right and top <= blue_y < bottom:
                    num = r * num_cols + c + 1  # 返回区域编号（从1开始）
                    if num == 1:
                        num = self.roomNum
                    return num
        return None

    def no_hero_handle(self, result=None, mov_time=0.3):
        """
        找不到英雄或卡墙了，随机移动，攻击几下
        """

        angle = (self.next_angle % 4) * 90 + \
            random.randrange(start=-15, stop=15)
        print(f'正在随机移动。。。随机角度移动{angle}度。')
        self.next_angle = (self.next_angle + 1) % 4
        sx, sy = self.ctrl.calc_mov_point(angle)
        self.move_to_xy(sx, sy)
        time.sleep(mov_time)
        self.ctrl.attack(3)

    def move_to_xy(self, x, y, out_time=2):
        """
        移动到指定位置,默认2秒超时
        """
        x = x + random.randint(-5, 5)
        y = y + random.randint(-5, 5)
        self.mov_start = False
        if not self.mov_start:
            self.mov_start = True
            self.adb.touch_end(x, y)
            time.sleep(0.03)
            self.adb.touch_start(x, y)

        else:
            self.adb.touch_move(x, y)

    def click(self, match):
        x, y, w, h = match['rect']
        self.ctrl.click((x + w / 2), (y + h / 2))

    def is_ready(self, skillIndex: int):
        # 获取当前用户的技能位置列表
        skill_position = self.ctrl.skill_mapping[self.ctrl.user][skillIndex]

        # 从中心点向四周扩散的偏移量
        offset = 30  # 可以调整这个值，根据实际情况

        # 判断技能是否冷却的阈值，当像素点小于这个阈值，说明技能正在冷却
        some_threshold = 550  # 可以根据实际情况调整这个阈值

        # 定义截图区域的裁剪范围
        crop = (
            skill_position[0] - offset, skill_position[1] - offset,
            skill_position[0] + offset, skill_position[1] + offset
        )

        # 获取屏幕截图并截取技能图标区域
        skill_icon = self.ctrl.adb.last_screen  # 确保是函数调用
        if skill_icon is None:
            print("未能获取屏幕截图，技能判断失败。")
            return False

        # 裁剪技能图标区域
        skill_icon = skill_icon[crop[1]:crop[3], crop[0]:crop[2]]

        # 将图标转换为灰度图像
        gray_icon = cv.cvtColor(skill_icon, cv.COLOR_BGR2GRAY)

        # 使用二值化处理，分离冷却遮罩
        _, thresholded = cv.threshold(gray_icon, 120, 255, cv.THRESH_BINARY)

        # 计算非零像素数量
        non_zero_pixels = cv.countNonZero(thresholded)
        print(f'技能{skillIndex}非零像素数量:{non_zero_pixels} 阈值:{some_threshold}')

        # 如果非零像素数量小于某个阈值，说明图标是灰色的，技能正在冷却
        if non_zero_pixels < some_threshold:
            print(f"技能 {skillIndex}，正在冷却中...")
            return False
        else:
            print(f"技能 {skillIndex}，完成冷却，可以释放")
            return True

    # 确认
    def match_confirm(self):
        crop = (1127, 643, 325, 130)
        crop = tuple(int(value * 1) for value in crop)
        result = image_match_util.match_template_best(
            self.CONFIRM, self.adb.last_screen, crop)
        if result:
            self.click(result)
            print("点击确认成功")
            time.sleep(6)

            return True
        else:
            print("No matches confirm")
            return False




    def perform_action(self, action_type: str, move_t: float, sx: int, sy: int, ax: int, ay: int, hx: int, hy: int):
        if action_type == 'attack':
            if self.roomNum in [14,15, 10,11]:
                self.ctrl.move(0,0.2)
            distance = math.sqrt((hx - ax) ** 2 + (hy - ay) ** 2)
            # 判断在一条直线上再攻击
            y_dis = abs(ay - hy)
            mov_to_master_start = time.time()
            print(f"距离最近的怪物：{distance}，判断是否再一条直线{y_dis}")
            if distance <= 600 and y_dis <= 100:
                # 面向敌人
                angle = calculate_angle(hx, hy, ax, hy)
                sx, sy = self.ctrl.calc_mov_point(angle)
                self.move_to_xy(sx, sy)
                # self.ctrl.move(angle, 0.3)
                print(
                    f'====================敌人与我的角度{angle}==攻击怪物，，当前房间,{self.roomNum}')
                if self.fixed_attack() is False:
                    # 普攻
                    self.ctrl.attack()
                if self.ctrl.user in ["KZ", "NM", "JH"]:
                    if self.fixed_attack() is False:
                        # 普攻
                        self.ctrl.attack()
                else:
                    self.ctrl.gq_fixed(self.roomNum)
                mov_to_master_start = time.time()

            # 怪物在右边,就走到怪物走边400的距离
            if ax > hx:
                ax = int(ax - 500)
            else:
                ax = int(ax + 500)
            angle = calculate_angle(hx, hy, ax, ay)
            sx, sy = self.ctrl.calc_mov_point(angle)
            # self.param.mov_start = False
            self.move_to_xy(sx, sy, 1)
            if time.time() - mov_to_master_start > 5:
                self.no_hero_handle(mov_time=1)
                mov_to_master_start = time.time()
        elif action_type == 'item':
            self.adb.tap(sx, sy, move_t)
            # self.move_to_xy(sx, sy, move_t)
        elif action_type == 'move':
            self.adb.tap(sx, sy, 2 if len(self.arrow) > 3 else move_t)
            # self.move_to_xy(sx, sy, move_t)
        elif action_type == 'goSZT':
            self.adb.tap(sx, sy, move_t)
        elif action_type == 'goDoor':
            if move_t > 1:
                self.ctrl.move(0, 0.3)
                return
            print('goDoor  ###############              ', move_t)
            self.adb.tap(sx, sy, move_t)


if __name__ == '__main__':
    ctrl = GameControl(ScrcpyADB(2400))
    action = GameAction(ctrl)

    while True:
        action.start()
        time.sleep(3)
