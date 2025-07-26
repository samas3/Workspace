# 📦 导入库
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import alsaaudio
import sounddevice as sd
import simpleaudio as sa
from scipy.io.wavfile import write
import numpy as np
from lib.DFRobot_RaspberryPi_DC_Motor import DFRobot_DC_Motor_IIC as Board
from PIL import Image, ImageOps
from lib import INA219
import cv2

from gpiozero import LED
from lib import LCD_1inch28
from gpiozero import PWMOutputDevice
from gpiozero import DistanceSensor
class PiHardware:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_hardware()
            self._initialized = True
    
    def _setup_hardware(self):
        self.led = LED(24)
        self.disp = LCD_1inch28.LCD_1inch28()
        self.disp.Init() # 点亮屏幕
        # Clear display.
        self.disp.clear()
        #Set the backlight to 50
        self.disp.bl_DutyCycle(50)
        # 电机速度控制（接 PWMA，即 GPIO13），仅能初始化一次
        self.pwm = PWMOutputDevice(13)
        # 注意配置引脚
        self.sensor = DistanceSensor(echo=6, trigger=26)

# 全局使用
def get_hardware():
    return PiHardware()
try:
    hardware = get_hardware()
    led, disp, pwm, sensor = hardware.led, hardware.disp, hardware.pwm, hardware.sensor
except Exception as e:
    print('❌ 初始化硬件失败:', e)
    print('LED, LCD, PWM, DistanceSensor 未初始化')
ina219 = INA219.INA219(addr=0x42)
board = Board(1, 0x10)    # RaspberryPi select bus 1, set address to 0x10

# 配置音频
# 设置 ALSA_CARD 为第一个 USB 输出设备的索引（如存在）
# 查找包含 'usb' 的音频输出设备
dev = next((d for d in sd.query_devices() if d['max_output_channels'] > 0 and 'usb' in d['name'].lower()), None)
# 设置 ALSA_CARD 环境变量以使用 USB 设备
if dev: os.environ['ALSA_CARD'] = str(dev['index'])
sd.default.latency = 'low'  # 减少延迟
sd.default.dtype = 'float32'  # 使用更高精度
# 设置音量，建议每次播放前都调整音量
m = alsaaudio.Mixer('Master')
def set_volume(volume):
    # 设置音量为 60%
    m.setvolume(volume)

def play_audio(file_path):
    set_volume(100)
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
def display_img(image):
    disp.ShowImage(image) # 显示图像
def display_pic(image_path):
    if not os.path.exists(image_path):
        print(f"Error: Image {image_path} does not exist.")
        return
    # Load and display the image# 读取并打开图像文件
    image = Image.open(image_path)
    image = image.rotate(270)

    image = ImageOps.fit(image, (240, 240), method=Image.LANCZOS, centering=(0.5, 0.5))
    # 显示图像
    display_img(image)
def record(fs, duration, path="media/test_mic.wav"):
    # CHUNK = 1024
    # FORMAT = pyaudio.paInt16
    # CHANNELS = 2
    # RATE = fs
    # RECORD_SECONDS = duration
    # WAVE_OUTPUT_FILENAME = path

    # p = pyaudio.PyAudio()

    # stream = p.open(format=FORMAT,
    #                 channels=CHANNELS,
    #                 rate=RATE,
    #                 input=True,
    #                 frames_per_buffer=CHUNK)

    # print("* recording")

    # frames = []

    # for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    #     data = stream.read(CHUNK)
    #     frames.append(data)

    # print("* done recording")

    # stream.stop_stream()
    # stream.close()
    # p.terminate()

    # wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    # wf.setnchannels(CHANNELS)
    # wf.setsampwidth(p.get_sample_size(FORMAT))
    # wf.setframerate(RATE)
    # wf.writeframes(b''.join(frames))
    # wf.close()

    print("* 开始录音")
    os.system('amixer -c 0 cset numid=3 7 > /dev/null 2>&1')
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1) # 录制音频
    sd.wait() # 等待录音完成
    print("* 录音结束")

    #将浮点格式转换为整数格式
    myrecording = np.int16(myrecording / np.max(np.abs(myrecording)) * 32767)

    # 保存音频文件
    write(path, fs, myrecording)
def get_distance_cm():
    return sensor.distance * 100  # 返回的是 m，需要乘100变成 cm
def capture_photo(path="media/output.jpg"):
    """执行拍照并保存图片"""
    # 初始化摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 摄像头无法打开")
    for _ in range(5):  # 先热身几帧
        cap.read()

    ret, frame = cap.read()
    cap.release()

    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # image = Image.fromarray(frame_rgb)
        # image = image.resize((320, 240))  # 缩放为 320x240
        # disp.ShowImage(image)  # 显示图像
        cv2.imwrite(path, frame)
        print("✅ 拍照成功，图片保存为 test_camera.jpg")
    else:
        print("❌ 拍照失败")

def stop_radar(): 
    pwm.off()
def set_radar_speed(speed):
    """设置雷达速度"""
    if 0 <= speed <= 1:
        pwm.value = speed
        print(f"雷达速度设置为 {speed * 100}%")
    else:
        print("❌ 错误：速度必须在 0 到 1 之间")
def get_cpu_temp():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp_str = f.readline()
    return float(temp_str) / 1000  # 单位是°C

def get_battery():
    bus_voltage = ina219.getBusVoltage_V()             # 获取负载侧的总线电压（V-端的电压）
    shunt_voltage = ina219.getShuntVoltage_mV() / 1000 # 获取分流电阻两端电压（V+ 与 V- 之间），单位换算为伏特
    current = ina219.getCurrent_mA()                   # 获取通过分流电阻的电流，单位为毫安（mA）
    power = ina219.getPower_W()                        # 获取功率，单位为瓦特（W）

    # 将电压映射为一个百分比，通常用于电量或亮度等显示（6V 映射为 0%，8.4V 映射为 100%）
    p = (bus_voltage - 6)/2.4*100
    if(p > 100): p = 100                               # 超过100%则限制为100%
    if(p < 0): p = 0                                   # 小于0%则限制为0%

    # INA219 测量的是负载端（V-）的电压，因此电源电压 = bus_voltage + shunt_voltage
    # print("PSU Voltage:   {:6.3f} V".format(bus_voltage + shunt_voltage)) # 如需显示电源端电压可取消注释
    # print("Shunt Voltage: {:9.6f} V".format(shunt_voltage))              # 如需显示分流电压可取消注释

    # print("Load Voltage:  {:6.3f} V".format(bus_voltage))           # 打印负载电压
    # print("Current:       {:9.6f} A".format(current/1000))          # 打印电流（单位换算为安培）
    # print("Power:         {:6.3f} W".format(power))                 # 打印功率
    # print("Percent:       {:3.1f}%".format(p))                      # 打印映射后的百分比数值
    return bus_voltage, current/1000, power, p