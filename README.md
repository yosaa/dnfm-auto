## 基于yolov5模型实现布万家自动化搬砖
### 项目根目录的demo_video.pm4为演示视频
![demo_video2gif](https://github.com/yosaa/dnfm-auto/blob/main/demo_video.gif)

### 代码已经全部开源

### 启动方式：
1. 安装所需依赖库
2. 进入游戏布万加副本
4. 任意软件投屏到电脑 （例如Scrcpy、QtScrcpy、py-scrcpy）
5. 将main.py中的 window_title 修改为自己投屏窗口的名称
5. 执行命令  python main.py

#### 如果点击的位置不正确，可以自行修改game_control.py中的坐标
1. 按技能范围配置 self.skill_coordinates 
2. 按职业固定技能键位 self.skill_mapping
3. 移动轮盘中心点百分比坐标  def calc_mov_point(self, angle: float) 
4. 普通攻击百分比坐标 def attack(self, t: float = 0.01)
5. 再次挑战键位百分比坐标 def click_again(self)
6. 小地图百分比坐标  def click_map(self)

上述均为百分比坐标，例如投屏窗口高H,宽W,当前点位坐标（X, Y）,则百分比坐标为 （X / W, Y / H）
配置一次，可以在任意电脑上运行，每个手机长宽比固定

### 已实现功能

- 识别图像中人物、怪物、材料、门等物体
- 自动寻路、过图
- 固定人物攻击逻辑
- 根据怪物数量攻击逻辑
- 识别狮子头房间
- 开局使用buff技能
- 拾取材料等掉落物（支持粉装掉落识别）
- 自动再次挑战

### 待优化
1. 寻路箭头在脚底时，移动方向有误 （已优化）
2. 大量怪物贴脸围殴时，需要尝试触发后撤步脱离
3. 效率较低，需要配置人物固定房间、固定打法 （已优化，配置奶妈，鬼泣固定打法）
5. 投屏方案占用鼠标，仅作为思路参考


#### 上传的权重文件仅支持部分人物，如果识别不准确，可以按照以下教程自己训练
#### 标注工具
[Label Studio Documentation — Quick start guide for Label Studio](https://labelstud.io/guide/quick_start)

标注工具启动方式：
```
 label-studio start
```

#### yolov5所需分类
```
['Gate' # 门,'Hero' # 玩家人物,'Item' # 掉落物品,'Mark' # 箭头标记,'Monster' # 怪物,'Monster_Fake' # 怪物尸体]
```

#### pt转ncnn步骤
```
yolov5根目录
python export.py --weights best.pt --img 460 --batch 1 --train
python -m onnxsim best.onnx best-sim.onnx
使用官方转化工具
./onnx2ncnn ./model/best-sim.onnx model/best.param model/best.bin
```

##### 本项目不参与商业用途，仅供学习参考
##### 如果有好的建议和方案，欢迎找我讨论，绿色泡泡：yosaaqwq (注明添加来源，否则不通过，伸手党绕路)
