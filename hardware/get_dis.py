#功能：避障
from gpiozero import DistanceSensor
from gpiozero import PWMOutputDevice

import os
import sys
# 添加父目录到 sys.path，使得 lib 可以被正确导入
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.DFRobot_RaspberryPi_DC_Motor import DFRobot_DC_Motor_IIC as Board
import ydlidar
import numpy as np
import time

# 初始化超声波传感器
ultrasonic = DistanceSensor(echo=6, trigger=26)

# 初始化电机控制
board = Board(1, 0x10)
if board.begin() != board.STA_OK:
    print("board begin failed")
    exit()
else:
    print("board begin success")
    board.set_encoder_enable(board.ALL)
    board.set_encoder_reduction_ratio(board.ALL, 43)
    board.set_moter_pwm_frequency(1000)

# 初始化雷达
ydlidar.os_init()
laser = ydlidar.CYdLidar()
laser.setlidaropt(ydlidar.LidarPropSerialPort, "/dev/ttyAMA2")
laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 115200)
laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
laser.setlidaropt(ydlidar.LidarPropScanFrequency, 4.0)
laser.setlidaropt(ydlidar.LidarPropSampleRate, 3)
laser.setlidaropt(ydlidar.LidarPropSingleChannel, True)

if not laser.initialize() or not laser.turnOn():
    print("Lidar initialization failed")
    exit()

# 避障参数设置
SAFE_DISTANCE = 0.2  # 安全距离(米)

def get_front_obstacle_distance():
    """获取前方障碍物距离"""
    # 超声波测距
    us_distance = ultrasonic.distance
    
    # 雷达测距(前方90度范围)
    scan = ydlidar.LaserScan()
    if laser.doProcessSimple(scan):
        points = scan.points
        front_ranges = []
        for p in points:
            # 转换为角度(-45到45度为前方)
            angle_deg = np.degrees(p.angle)
            if -45 <= angle_deg <= 45:
                front_ranges.append(p.range)
        
        if front_ranges:
            lidar_distance = min(front_ranges)
            if lidar_distance != 0:
            # 取超声波和雷达的最小距离作为前方障碍物距离
                return min(us_distance, lidar_distance)
            else:
                return us_distance
    
    return us_distance