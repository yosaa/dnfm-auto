## 基于 YOLOv5 模型实现布万家自动化搬砖

## 项目演示

项目根目录的 `demo_video.pm4` 为演示视频  
![演示视频](https://github.com/yosaa/dnfm-auto/blob/main/demo_video.gif)

#### main分支：实现基础功能的简易代码，安装依赖即可运行。基于此可进行优化，增添功能
#### test分支：调优过程中的测试代码，不可直接运行。包含教程中提到的功能，仅供思路参考
#### 关注、收藏，后续更新完整项目，可以第一时间收到通知

## 简略说明 | [详细步骤01](./doc/逐行代码讲解_01.md)|[详细步骤02](https://www.zhihu.com/people/luo-mai-qing)

## 启动方式

1. **安装所需依赖库**
2. **进入游戏布万加副本**
3. **投屏到电脑**  
   使用任意软件投屏到电脑（例如 Scrcpy、QtScrcpy、py-scrcpy）
4. **修改投屏窗口名称**  
   将 `main.py` 中的 `window_title` 修改为投屏窗口的名称
5. **运行项目**  
   执行命令：  
   
   ```bash
   python main.py
   ```



## 定位和调整

如果点击的位置不正确，可以通过修改 `game_control.py` 中的坐标进行调整：

1. **技能范围配置**  
   修改 `self.skill_coordinates`
2. **职业固定技能键位**  
   修改 `self.skill_mapping`
3. **移动轮盘中心点百分比坐标**  
   修改 `def calc_mov_point(self, angle: float)`
4. **普通攻击百分比坐标**  
   修改 `def attack(self, t: float = 0.01)`
5. **再次挑战键位百分比坐标**  
   修改 `def click_again(self)`
6. **小地图百分比坐标**  
   修改 `def click_map(self)`

手机屏幕截个图，用电脑自带的画图工具打开，左下角会显示当前鼠标位置坐标。
所有坐标均为百分比坐标，例如投屏窗口高 `H`，宽 `W`，当前点位坐标为 `(X, Y)`，则百分比坐标为 `(X / W, Y / H)`。配置完成后，可以在任意电脑上运行，每个手机的长宽比固定。

## 已实现功能

- **图像识别**：识别图像中的人物、怪物、材料、门等物体
- **自动寻路与过图**
- **固定人物攻击逻辑**
- **根据怪物数量调整攻击逻辑**
- **识别狮子头房间**
- **开局使用 Buff 技能**
- **拾取材料等掉落物**（支持粉装掉落识别）
- **自动再次挑战**

## 待优化事项

1. **寻路方向问题**：当寻路箭头在脚底时，移动方向有误（已优化）
2. **怪物围殴处理**：大量怪物贴脸围殴时，需要尝试触发后撤步脱离
3. **效率提升**：需要配置人物固定房间、固定打法（已优化，配置奶妈，鬼泣固定打法）
4. **投屏方案限制**：投屏方案占用鼠标，仅作为思路参考

## 

## 自定义模型训练

上传的权重文件仅支持测试角色，如果识别不准确，可以按照以下教程自行训练模型。

### 标注工具

[Label Studio Documentation — Quick start guide for Label Studio](https://labelstud.io/guide/quick_start)

标注工具启动方式：

```bash
label-studio start
```

### YOLOv5 所需分类

```python
['Gate' # 门, 'Hero' # 玩家人物, 'Item' # 掉落物品, 'Mark' # 箭头标记, 'Monster' # 怪物, 'Monster_Fake' # 怪物尸体]
```

### pt 转 ncnn 步骤

```bash
# 在 YOLOv5 根目录执行以下命令
python export.py --weights best.pt --img 460 --batch 1 --train
python -m onnxsim best.onnx best-sim.onnx

# 使用官方转换工具
./onnx2ncnn ./model/best-sim.onnx model/best.param model/best.bin
```

## 注意事项

- 本项目不参与商业用途，仅供学习参考。
- 如有帮助记得给个星星，方便后续更新提醒。
- 基础问题百度都可以解决，实在有不明白或者有思路想探讨，可➕绿色泡泡：`yosaaqwq`  
  （**添加时请注明来源，否则不通过，伸手党请绕路**）
