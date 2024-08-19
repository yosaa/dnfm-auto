import pygetwindow as gw
from PIL import ImageGrab
import cv2 as cv
import time
import pyautogui
from .yolov5 import YoloV5s


class scrcpyQt:
    def __init__(self, window_title):
        self.window_title = window_title
        self.yolo = YoloV5s(target_size=640,
                            prob_threshold=0.25,
                            nms_threshold=0.45,
                            num_threads=4,
                            use_gpu=True)
        self.windowsInfo = (0, 0, 0, 0)
        pyautogui.FAILSAFE = False

    # 定义一个名为on_frame的方法，这个方法属于一个类，因为使用了self参数
    def on_frame(self):
        try:
            # 尝试执行以下代码块
            # gw是getwindows的缩写，可能是一个获取窗口列表的函数或方法
            # getWindowsWithTitle是一个方法，用于获取所有包含指定标题的窗口
            # self.window_title是类的一个属性，存储了要捕获的窗口的标题
            # [0]表示获取列表中的第一个窗口，假设只有一个窗口匹配
            window = gw.getWindowsWithTitle(self.window_title)[0]
            
            # 检查是否成功获取到了窗口对象
            if window:
                # 如果获取到了窗口，调用其restore方法，可能是还原窗口大小
                window.restore()
                # 调用其activate方法，激活窗口，使其成为当前窗口
                window.activate()
                # 使用time.sleep暂停0.1秒，等待窗口完全激活
                time.sleep(0.1)  # 等待窗口完全激活

                # 获取窗口的位置和大小信息
                # left, top是窗口左上角的坐标
                # width, height是窗口的宽度和高度
                x, y, width, height = window.left, window.top, window.width, window.height
                
                # 将窗口的位置和大小信息存储到self.windowsInfo属性中
                self.windowsInfo = (x, y, width, height)

                # 使用ImageGrab模块的grab方法来截取指定窗口的屏幕图像
                # bbox参数定义了截图的边界框，即窗口的左上角坐标和右下角坐标
                screen = ImageGrab.grab(bbox=(x, y, x + width, y + height))
                # 函数返回截取的屏幕图像
                return screen
            
        # 捕获并处理在执行上述代码时可能发生的任何异常
        except Exception as e:
            # 打印异常信息
            print(f"An error occurred: {e}")

    def touch_start(self, x: int or float, y: int or float):
        pyautogui.moveTo(x, y, duration=0.4)  # 移动到指定位置，持续时间0.4秒
        pyautogui.mouseDown()  # 模拟按下

    def touch_move(self, x: int or float, y: int or float):
        pyautogui.moveTo(x, y, duration=0.25)

    def touch_end(self, x: int or float, y: int or float):
        pyautogui.mouseUp()

    def tap(self, x: int or float, y: int or float, t: float = 0.01):
        self.touch_start(x, y)
        time.sleep(t)
        self.touch_end(x, y)

if __name__ == "__main__":
    window_title = "Phone-f0d62d51"
