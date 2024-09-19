import time
import cv2 as cv
from dnfm.game_control import GameControl
from dnfm.scrcpy_adb_qt import ScrcpyADB
from dnfm.game_action import GameAction
from dnfm.utils.cvmatch import image_match_util

def match_heroes(screen):
    hero_images = [
        cv.imread('template/judgingRoles/kuangzhan.jpg'),
        cv.imread('template/judgingRoles/naima.png'),
        cv.imread('template/judgingRoles/qiangpao.png'),
        cv.imread('template/judgingRoles/guiqi.png'),
        cv.imread('template/judgingRoles/axiuluo.png'),
        cv.imread('template/judgingRoles/jianhun.jpg')
    ]
    hero_names_zh = ["狂战士", "奶妈", "枪炮", "鬼泣", "阿修罗", "剑魂"]
    hero_names = ["KZ", "NM", "QP", "GQ", "AXL", "JH"]
    results = []
    crop = (100, 10, 140, 110)
    crop = tuple(int(value * 1) for value in crop)
    # 遍历所有英雄图像并匹配
    for i, hero in enumerate(hero_images):
        result = image_match_util.match_template_best(hero, screen, crop)
        if result:
            result['hero_name'] = hero_names[i]  # 添加英雄名字到结果中
            results.append(result)

    # 如果找到匹配结果，选择置信度最高的匹配
    if results:
        best_match = max(results, key=lambda r: r['confidence'])
        current_hero = best_match['hero_name']
        current_hero_zh = hero_names_zh[hero_names.index(current_hero)]
        return current_hero, current_hero_zh
    else:
        print("No matches found.")
        return None, None

def main():

    sadb = ScrcpyADB(2400)
    ctrl = GameControl(sadb)
    action = GameAction(ctrl)

    while True:
        time.sleep(1)
        if action.adb.last_screen is None:
            continue

        current_hero, current_hero_zh = match_heroes(action.adb.last_screen)
        if current_hero:
            print(f"当前角色是: {current_hero_zh} ")
            action.ctrl.user = current_hero
            break

    # 启动子线程         
    action.start_thread()
    # 启动服务
    while True:
        action.start()


if __name__ == '__main__':
    main()
