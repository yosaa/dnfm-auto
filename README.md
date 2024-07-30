## 基于yolov5模型实现布万家自动化搬砖
### 项目根目录的![demo_video.pm4](./demo_video.mp4)为演示视频
![demo_video2gif]([./demo_video.mp4](https://github.com/yosaa/dnfm-auto/blob/main/demo_video.gif))

### 2024年07月30日，跑图效率不及预期，最佳情况也需要2分30秒+，实用性不高，暂不考虑继续更新

### 代码已经全部开源，根目录放入yolo转ncnn的权重文件.bin与.param文件，即可运行

#### 标注工具
[Label Studio Documentation — Quick start guide for Label Studio](https://labelstud.io/guide/quick_start)

启动方式：
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

### 已实现功能

- 识别图像中人物、怪物、材料、门等物体
- 自动寻路、过图
- 固定人物攻击逻辑
- 根据怪物数量攻击逻辑
- 识别狮子头房间
- 开局使用buff技能
- 拾取材料等掉落物（支持粉装掉落识别）
- 自动再次挑战
- 

### 待优化
1. 寻路箭头在脚底时，移动方向有误 （已优化）
2. 大量怪物贴脸围殴时，需要尝试触发后撤步脱离
3. 效率较低，需要配置人物固定房间、固定打法 （已优化，配置奶妈，鬼泣固定打法）
4. 模型识别不够精确，训练集数量过少

##### 本项目不参与商业用途，仅供学习参考
##### 如果有好的建议和方案，欢迎找我讨论，绿色泡泡：yosaaqwq (注明添加来源，否则不通过)
