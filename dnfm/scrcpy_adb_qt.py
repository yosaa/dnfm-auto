import pygetwindow as gw
from PIL import ImageGrab
import cv2 as cv
import numpy as np
import time
import pyautogui
from yolov5 import YoloV5s


class scrcpyQt:
    def __init__(self, window_title):
        self.window_title = window_title
        self.yolo = YoloV5s(target_size=640,
                            prob_threshold=0.25,
                            nms_threshold=0.45,
                            num_threads=4,
                            use_gpu=True)
        # self.device = torch.device(
        #     'cuda' if torch.cuda.is_available() else 'cpu')
        # self.yolo = torch.hub.load('D:/yolo/dnfm-yolo-tutorial-master/yolov5', 'custom',
        #                            'D:/yolo/dnfm-yolo-tutorial-master/yolov5/best.pt', source='local').to(self.device)
        self.windowsInfo = (0, 0, 0, 0)
        pyautogui.FAILSAFE = False

    def on_frame(self):
        try:
            window = gw.getWindowsWithTitle(self.window_title)[0]
            if window:
                window.restore()
                window.activate()
                time.sleep(0.1)  # 等待窗口完全激活

                x, y, width, height = window.left, window.top, window.width, window.height
                self.windowsInfo = (x, y, width, height)

                screen = ImageGrab.grab(bbox=(x, y, x + width, y + height))
                screen_np = cv.cvtColor(np.array(screen), cv.COLOR_RGB2BGR)
                # self.last_screen = screen_np
                return screen
        except Exception as e:
            print(f"An error occurred: {e}")

    def getXY(self, screen_np):
        try:
            result = self.yolo(screen_np)
            for obj in result:
                color = (0, 255, 0)
                if obj.label == 1:
                    color = (255, 0, 0)
                elif obj.label == 5:
                    color = (0, 0, 255)
                else:
                    color = (0, 0, 255)

                cv.rectangle(screen_np,
                             (int(obj.rect.x), int(obj.rect.y)),
                             (int(obj.rect.x + obj.rect.w),
                              int(obj.rect.y + + obj.rect.h)),
                             color, 2
                             )
            # cv.imshow('frame', screen_np)
            # cv.waitKey(3000)
        except Exception as e:
            print(e)

    def touch_start(self, x: int or float, y: int or float):
        pyautogui.moveTo(x, y, duration=0.4)  # 移动到指定位置，持续时间0.25秒
        pyautogui.mouseDown()  # 模拟按下

    def touch_move(self, x: int or float, y: int or float):
        pyautogui.moveTo(x, y, duration=0.25)

    def touch_end(self, x: int or float, y: int or float):
        pyautogui.mouseUp()

    def tap(self, x: int or float, y: int or float, t: float = 0.01):
        self.touch_start(x, y)
        time.sleep(t)
        self.touch_end(x, y)

    def compare_images_flann(main_image_path, sub_image_path):
        # 读取图片
        main_image = cv2.imread(main_image_path, cv2.IMREAD_GRAYSCALE)
        sub_image = cv2.imread(sub_image_path, cv2.IMREAD_GRAYSCALE)

        # 检查图片是否正确加载
        if main_image is None or sub_image is None:
            print("Error: 图片加载失败，请检查路径是否正确")
            return False

        # 使用SIFT算法提取特征点
        sift = cv2.SIFT_create()
        keypoints1, descriptors1 = sift.detectAndCompute(main_image, None)
        keypoints2, descriptors2 = sift.detectAndCompute(sub_image, None)

        # 如果特征点数量太少，则认为匹配失败
        if len(keypoints1) < 10 or len(keypoints2) < 10:
            print("Error: 特征点数量太少，无法进行匹配")
            return False

        # 使用FLANN匹配器进行特征匹配
        flann = cv2.FlannBasedMatcher()
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


def main():
    window_title = "Phone-f0d62d51"



if __name__ == "__main__":
    main()
