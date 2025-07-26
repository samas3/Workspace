#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开机自动启动脚本
功能: LED控制、音频播放、雷达电机控制、屏幕显示状态信息
"""

import os
import time
import socket
import subprocess
import alsaaudio
import sounddevice as sd
import simpleaudio as sa
from time import sleep
from gpiozero import LED, PWMOutputDevice
from PIL import Image, ImageDraw, ImageFont

# 主函数
import main

# 导入自定义库
try:
    from lib import LCD_1inch28
    from lib import INA219
    from lib.DFRobot_RaspberryPi_DC_Motor import DFRobot_DC_Motor_IIC as Board
except ImportError as e:
    print(f"导入库失败: {e}")
    exit(1)

class SystemManager:
    """系统管理类，集成所有硬件控制功能"""
    
    def __init__(self):
        self.led = None
        self.disp = None
        self.ina219 = None
        self.motor_board = None
        self.pwm_motor = None
        self.mixer = None
        
    def initialize_hardware(self):
        """初始化所有硬件设备"""
        print("🔧 开始初始化硬件...")
        
        # 初始化LED
        try:
            self.led = LED(24)
            print("✅ LED初始化成功")
        except Exception as e:
            print(f"❌ LED初始化失败: {e}")
        
        # 配置音频设备
        self._setup_audio()
        
        # 初始化LCD屏幕
        try:
            self.disp = LCD_1inch28.LCD_1inch28()
            self.disp.Init()
            self.disp.clear()
            self.disp.bl_DutyCycle(50)  # 设置背光亮度50%
            print("✅ LCD屏幕初始化成功")
        except Exception as e:
            print(f"❌ LCD屏幕初始化失败: {e}")
        
        # 初始化电量监测
        try:
            self.ina219 = INA219.INA219(addr=0x42)
            print("✅ 电量监测初始化成功")
        except Exception as e:
            print(f"❌ 电量监测初始化失败: {e}")
        
        # 初始化电机控制板
        try:
            self.motor_board = Board(1, 0x10)
            if self.motor_board.begin() == self.motor_board.STA_OK:
                print("✅ 电机控制板初始化成功")
            else:
                print("❌ 电机控制板初始化失败")
                self.motor_board = None
        except Exception as e:
            print(f"❌ 电机控制板初始化失败: {e}")
        
        # 初始化PWM电机控制
        try:
            self.pwm_motor = PWMOutputDevice(13)
            print("✅ PWM电机控制初始化成功")
        except Exception as e:
            print(f"❌ PWM电机控制初始化失败: {e}")
        
        print("🎉 硬件初始化完成\n")
    
    def _setup_audio(self):
        """配置音频设备"""
        try:
            # 查找USB音频设备
            dev = next((d for d in sd.query_devices() 
                       if d['max_output_channels'] > 0 and 'usb' in d['name'].lower()), None)
            if dev:
                os.environ['ALSA_CARD'] = str(dev['index'])
            
            # 初始化音频混合器
            self.mixer = alsaaudio.Mixer('Master')
            print("✅ 音频设备配置成功")
        except Exception as e:
            print(f"❌ 音频设备配置失败: {e}")
    
    def led_test(self, duration=2):
        """LED测试：开灯指定时间后关灯"""
        if not self.led:
            print("❌ LED未初始化")
            return
        
        print(f"💡 LED开启 {duration} 秒...")
        self.led.on()
        sleep(duration)
        self.led.off()
        print("💡 LED关闭")
    
    def play_test_audio(self, volume=80):
        """播放测试音频"""
        if not self.mixer:
            print("❌ 音频混合器未初始化")
            return
        
        try:
            # 设置音量
            self.mixer.setvolume(volume)
            
            # 播放系统测试音频
            audio_path = "/home/pi/Workspace/media/test.wav"
            if os.path.exists(audio_path):
                print(f"🔊 播放测试音频 (音量: {volume}%)")
                wave_obj = sa.WaveObject.from_wave_file(audio_path)
                play_obj = wave_obj.play()
                play_obj.wait_done()
                print("🔊 音频播放完成")
            else:
                print("❌ 测试音频文件不存在")
        except Exception as e:
            print(f"❌ 音频播放失败: {e}")
    
    def stop_radar_motor(self):
        """关闭雷达电机"""
        if self.pwm_motor:
            try:
                self.pwm_motor.off()
                print("🛑 雷达电机已停止")
            except Exception as e:
                print(f"❌ 停止雷达电机失败: {e}")
        
        if self.motor_board:
            try:
                self.motor_board.motor_stop(self.motor_board.ALL)
                print("🛑 DC电机已停止")
            except Exception as e:
                print(f"❌ 停止DC电机失败: {e}")
    
    def get_system_info(self):
        """获取系统信息"""
        info = {}
        
        # 获取IP地址
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info['ip'] = s.getsockname()[0]
            s.close()
        except:
            info['ip'] = "未连接"
        
        # 获取CPU温度
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp_str = f.readline()
            info['cpu_temp'] = float(temp_str) / 1000
        except:
            info['cpu_temp'] = 0
        
        # 获取电量信息
        if self.ina219:
            try:
                bus_voltage = self.ina219.getBusVoltage_V()
                current = self.ina219.getCurrent_mA()
                power = self.ina219.getPower_W()
                
                # 计算电量百分比 (6V-8.4V映射到0-100%)
                battery_percent = (bus_voltage - 6) / 2.4 * 100
                battery_percent = max(0, min(100, battery_percent))
                
                info['voltage'] = bus_voltage
                info['current'] = current / 1000  # 转换为安培
                info['power'] = power
                info['battery_percent'] = battery_percent
            except:
                info['voltage'] = 0
                info['current'] = 0
                info['power'] = 0
                info['battery_percent'] = 0
        else:
            info['voltage'] = 0
            info['current'] = 0
            info['power'] = 0
            info['battery_percent'] = 0
        
        return info
    
    def create_status_image(self, info):
        """创建状态显示图像"""
        # 创建240x240的图像
        img = Image.new('RGB', (240, 240), color='black')
        draw = ImageDraw.Draw(img)
        
        try:
            # 尝试使用系统字体
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            # 如果字体加载失败，使用默认字体
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # 绘制标题
        draw.text((120, 20), "System", font=font_large, fill='white', anchor='mm')
        
        # 绘制IP地址
        draw.text((20, 60), f"IP: {info['ip']}", font=font_medium, fill='cyan')
        
        # 绘制温度
        temp_color = 'red' if info['cpu_temp'] > 70 else 'yellow' if info['cpu_temp'] > 50 else 'green'
        draw.text((20, 85), f"CPU Temp: {info['cpu_temp']:.1f}°C", font=font_medium, fill=temp_color)
        
        # 绘制电量信息
        battery_color = 'red' if info['battery_percent'] < 20 else 'yellow' if info['battery_percent'] < 50 else 'green'
        draw.text((20, 110), f"Battery: {info['battery_percent']:.1f}%", font=font_medium, fill=battery_color)
        draw.text((20, 135), f"Voltage: {info['voltage']:.2f}V", font=font_small, fill='white')
        draw.text((20, 155), f"Current: {info['current']:.3f}A", font=font_small, fill='white')
        draw.text((20, 175), f"Power: {info['power']:.2f}W", font=font_small, fill='white')
        
        # 绘制电量条
        bar_x, bar_y, bar_w, bar_h = 20, 200, 200, 20
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], outline='white', width=2)
        fill_w = int(bar_w * info['battery_percent'] / 100)
        if fill_w > 0:
            draw.rectangle([bar_x + 2, bar_y + 2, bar_x + fill_w - 2, bar_y + bar_h - 2], fill=battery_color)
        
        return img
    
    def display_status(self):
        """在屏幕上显示系统状态"""
        if not self.disp:
            print("❌ LCD屏幕未初始化")
            return
        
        try:
            info = self.get_system_info()
            img = self.create_status_image(info).rotate(270)
            self.disp.ShowImage(img)
            
            print("📊 系统状态:")
            print(f"   IP地址: {info['ip']}")
            print(f"   CPU温度: {info['cpu_temp']:.1f}°C")
            print(f"   电量: {info['battery_percent']:.1f}% ({info['voltage']:.2f}V)")
            print(f"   电流: {info['current']:.3f}A")
            print(f"   功率: {info['power']:.2f}W")
            
        except Exception as e:
            print(f"❌ 显示状态失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        print("\n🧹 正在清理资源...")
        
        if self.led:
            self.led.close()
        
        if self.pwm_motor:
            self.pwm_motor.close()
        
        if self.motor_board:
            try:
                self.motor_board.motor_stop(self.motor_board.ALL)
            except:
                pass
        
        print("✅ 资源清理完成")

def func():
    """主函数"""
    print("🚀 系统启动脚本开始运行...")
    print(f"⏰ 启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建系统管理器
    system = SystemManager()
    
    try:
        # 初始化硬件
        system.initialize_hardware()
        
        # 执行启动序列
        print("📋 执行启动序列:")

        # 1. 显示系统状态
        system.display_status()
        
        # 2. LED测试
        system.led_test(duration=2)

        # 3. 停止电机
        system.stop_radar_motor()
        
        # 4. 播放测试音频
        system.play_test_audio(volume=60)
        
        print("🎉 启动序列完成!")
        
        time.sleep(5)

    except Exception as e:
        print(f"❌ 运行时错误: {e}")
    
    finally:
        system.cleanup()
        print("👋 程序结束")
        # main.main()

if __name__ == "__main__":
    func()