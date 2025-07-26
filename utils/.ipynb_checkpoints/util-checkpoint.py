# 📦 导入库
import os
import time
import alsaaudio
import sounddevice as sd
import simpleaudio as sa
# 初始化代码，仅需执行一次

# 📦 导入库
from scipy.io.wavfile import write
import numpy as np

# 配置音频
# 设置 ALSA_CARD 为第一个 USB 输出设备的索引（如存在）
# 查找包含 'usb' 的音频输出设备
dev = next((d for d in sd.query_devices() if d['max_output_channels'] > 0 and 'usb' in d['name'].lower()), None)
# 设置 ALSA_CARD 环境变量以使用 USB 设备
if dev: os.environ['ALSA_CARD'] = str(dev['index'])
# 初始化 IO，仅能执行一次
from gpiozero import LED
led = LED(24)
# 设置音量，建议每次播放前都调整音量
m = alsaaudio.Mixer('PCM')
# 设置音量为 60%
m.setvolume(60)

# 初始化代码，仅需执行一次

# 📦 导入库
from lib.DFRobot_RaspberryPi_DC_Motor import DFRobot_DC_Motor_IIC as Board
board = Board(1, 0x10)    # RaspberryPi select bus 1, set address to 0x10

# 播放测试音频
# 加载并播放音频文件
def play_audio(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return
    # 播放音频文件
    wave_obj = sa.WaveObject.from_wave_file(file_path)
    play_obj = wave_obj.play()
    play_obj.wait_done()

if board.begin() != board.STA_OK:    # 初始化开发板并检查状态是否正常
    print("board begin faild")       # 如果初始化失败，打印失败信息
else:
    print("board begin success")     # 初始化成功，打印成功信息

    board.set_encoder_enable(board.ALL)                 # 启用所有电机的编码器
    # board.set_encoder_disable(board.ALL)              # （可选）禁用所有电机的编码器
    board.set_encoder_reduction_ratio(board.ALL, 43)    # 设置所有电机的编码器减速比（测试电机减速比为43.8）

    board.set_moter_pwm_frequency(1000)   # 设置电机的PWM频率为1000Hz
def stop_motor():
    board.motor_stop(board.ALL)   # stop all DC motor
# 初始化代码，仅能执行一次

from lib import LCD_1inch28
from PIL import Image

disp = LCD_1inch28.LCD_1inch28()
disp.Init() # 点亮屏幕

# Clear display.
disp.clear()
#Set the backlight to 50
disp.bl_DutyCycle(50)
def display_image(image_path):
    if not os.path.exists(image_path):
        print(f"Error: Image {image_path} does not exist.")
        return
    # Load and display the image# 读取并打开图像文件
    image = Image.open(image_path)
    image = image.rotate(270)

    # 显示图像
    disp.ShowImage(image) # 显示图像
def record(fs, duration):
    fs = 44100 # 采样频率

    print("* 开始录音")
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1) # 录制音频
    sd.wait() # 等待录音完成
    print("* 录音结束")

    # 将浮点格式转换为整数格式
    myrecording = np.int16(myrecording / np.max(np.abs(myrecording)) * 32767)

    # 保存音频文件
    write("media/test_mic.wav", fs, myrecording)
# 初始化代码，仅能执行一次

# 导入库
from gpiozero import DistanceSensor
from time import sleep

# 注意配置引脚
sensor = DistanceSensor(echo=6, trigger=26)
def get_distance_cm():
    return sensor.distance * 100  # 返回的是 m，需要乘100变成 cm
# 📦 导入库
import cv2
from PIL import Image

# 初始化摄像头
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ 摄像头无法打开")
else:
    for _ in range(5):  # 先热身几帧
        cap.read()

    ret, frame = cap.read()
    cap.release()

    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # image = Image.fromarray(frame_rgb)
        # image = image.resize((320, 240))  # 缩放为 320x240
        # disp.ShowImage(image)  # 显示图像
        cv2.imwrite("media/test_camera.jpg", frame)
        print("✅ 拍照成功，图片保存为 test_camera.jpg")
    else:
        print("❌ 拍照失败")