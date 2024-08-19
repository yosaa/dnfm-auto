from dnfm.game_control import GameControl
from dnfm.scrcpy_adb_qt import scrcpyQt
from dnfm.game_action import GameAction


def main():
    # 设置窗口标题
    window_title = "Phone-f0d62d51"

    ctrl = GameControl(scrcpyQt(window_title), window_title)
    action = GameAction(ctrl)

    while True:
        action.start()


if __name__ == '__main__':
    main()