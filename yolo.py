#可以实时用摄像头检测前方的东西（后续可以加开始和停止的时间+语音播报）

from ultralytics import YOLO
import cv2
import time

# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services import voice
from utils import util
# 加载 YOLOv8 模型
model = YOLO("yolov8n.pt")  # 确保 yolov8n.pt 在正确路径

# 初始化摄像头（0 表示默认摄像头，如果有多个摄像头可以尝试 1, 2, ...）
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ 摄像头无法打开")
    exit()

ret, frame = cap.read()
frame = cv2.resize(frame, (640, 480))  # 缩小分辨率提高速度

print("✅ 摄像头已开启，按 'q' 退出")
tts = voice.TextToSpeech()
translation = {
    'person': '人',
    'bicycle': '自行车',
    'car': '汽车',
    'motorcycle': '摩托车',
    'airplane': '飞机',
    'bus': '公交车',
    'train': '火车',
    'truck': '卡车',
    'boat': '船',
    'traffic light': '交通灯',
    'fire hydrant': '消防栓',
    'stop sign': '停车标志',
    'parking meter': '停车收费表',
    'bench': '长椅',
    'bird': '鸟',
    'cat': '猫',
    'dog': '狗',
    'horse': '马',
    'sheep': '羊',
    'cow': '牛',
    'elephant': '大象',
    'bear': '熊',
    'zebra': '斑马',
    'giraffe': '长颈鹿',
    'backpack': '背包',
    'umbrella': '雨伞',
    'handbag': '手提包',
    'tie': '领带',
    'suitcase': '行李箱',
    'frisbee': '飞盘',
    'skis': '滑雪板',
    'snowboard': '滑雪板（单板）',
    'sports ball': '运动球',
    'kite': '风筝',
    'baseball bat': '棒球棒',
    'baseball glove': '棒球手套',
    'skateboard': '滑板',
    'surfboard': '冲浪板',
    'tennis racket': '网球拍',
    'bottle': '瓶子',
    'wine glass': '酒杯',
    'cup': '杯子',
    'fork': '叉子',
    'knife': '刀',
    'spoon': '勺子',
    'bowl': '碗',
    'banana': '香蕉',
    'apple': '苹果',
    'sandwich': '三明治',
    'orange': '橙子',
    'broccoli': '西兰花',
    'carrot': '胡萝卜',
    'hot dog': '热狗',
    'pizza': '披萨',
    'donut': '甜甜圈',
    'cake': '蛋糕',
    'chair': '椅子',
    'couch': '沙发',
    'potted plant': '盆栽植物',
    'bed': '床',
    'dining table': '餐桌',
    'toilet': '马桶',
    'tv': '电视',
    'laptop': '笔记本电脑',
    'mouse': '鼠标',
    'remote': '遥控器',
    'keyboard': '键盘',
    'cell phone': '手机',
    'microwave': '微波炉',
    'oven': '烤箱',
    'toaster': '烤面包机',
    'sink': '水槽',
    'refrigerator': '冰箱',
    'book': '书',
    'clock': '时钟',
    'vase': '花瓶',
    'scissors': '剪刀',
    'teddy bear': '泰迪熊',
    'hair drier': '吹风机',
    'toothbrush': '牙刷'
}
while True:
    # 读取摄像头画面
    ret, frame = cap.read()
    if not ret:
        print("❌ 无法读取摄像头画面")
        break

    # 使用 YOLOv8 进行目标检测
    results = model(frame, conf=0.4)  # conf 是置信度阈值

    # 获取图片的宽度和高度
    height, width = frame.shape[:2]
    print(util.get_distance_cm())  # 打印距离
    # 遍历检测结果
    for result in results:
        for box in result.boxes:
            # 获取检测框坐标 (x1, y1, x2, y2)
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            # 计算检测框的中心点
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            # 判断物体在画面中的位置（水平方向）
            if center_x < width / 3:
                x_position = "左前方"
            elif center_x > 2 * width / 3:
                x_position = "右前方"
            else:
                x_position = "正前方"

            # 判断物体距离（垂直方向）
            if center_y < height / 3 * 1:
                y_position = "近处"
            elif center_y > height / 3 * 2:
                y_position = "远处"
            else:
                y_position = "中距离"

            # 获取类别名称和置信度
            class_id = int(box.cls[0])
            class_name = result.names[class_id]
            confidence = float(box.conf[0])

            # 在画面上显示检测信息
            info = f"{translation.get(class_name, class_name)}在{x_position}{y_position}"
            # if y_position != "远处":
            #     tts.speak(info)
            #     util.play_audio('media/output.wav')
            #     time.sleep(0.5)
            print(info)

    # 显示检测结果
    #cv2.imshow("YOLOv8 实时检测 (按 q 退出)", frame)

    # 按 'q' 退出
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# 释放摄像头并关闭窗口
cap.release()
cv2.destroyAllWindows()



