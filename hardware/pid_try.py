import time
import sys
import os

# 添加父目录到 sys.path，使得 lib 可以被正确导入
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.DFRobot_RaspberryPi_DC_Motor import DFRobot_DC_Motor_IIC as Board

class PIDcontrolMove:
    def __init__(self):
        self.kp = 0.8
        self.ki = 0.05
        self.kd = 0.1
        self.last_error = 0
        self.integral = 0
    def compute(self, setpoint, measured_value):
        error = setpoint - measured_value
        self.integral += error
        derivative = error - self.last_error
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        self.last_error = error
        print("Err: %6f; Output: %6f" % (error, output))
        print("Setpoint: %6f; Measured: %6f" % (setpoint, measured_value))
        return output
    def clear(self):
        self.integral = 0
        self.last_error = 0

class MotorController:
    def __init__(self):
        self.board = Board(1, 0x10)
        if self.board.begin() != self.board.STA_OK:
            print("board begin fail")
        else:
            print("board begin success")
        self.board.set_encoder_enable(self.board.ALL)
        self.board.set_encoder_reduction_ratio(self.board.ALL, 43)
        self.board.set_moter_pwm_frequency(1000)
        self.move_speed = 50
        self.PIDcm = [PIDcontrolMove(), PIDcontrolMove()]
        self.zkb1 = self.zkb2 = 60
    def stop(self):
        self.board.motor_stop(self.board.ALL)
    def zf(self, speed):
        if speed == 0: return 1
        return abs(speed) / speed
    def PIDctrlMove(self):
        speed = self.board.get_encoder_speed(self.board.ALL)
        print(f"Encoder speeds: M1={speed[0]}, M2={speed[1]}")
        self.zkb1 += self.PIDcm[0].compute(self.move_speed * self.zf(speed[0]), speed[0])
        self.zkb2 += self.PIDcm[1].compute(self.move_speed * self.zf(speed[1]), speed[1])
        self.zkb1 = max(30, min(self.zkb1, 100))
        self.zkb2 = max(30, min(self.zkb2, 100))
    def forward(self, len):
        ed = time.time() + len / 13.5
        self.PIDcm[0].clear()
        self.PIDcm[1].clear()
        while time.time() < ed:
            self.board.motor_movement([self.board.M1], self.board.CCW, self.zkb1)
            self.board.motor_movement([self.board.M2], self.board.CW, self.zkb2)
            self.PIDctrlMove()
            print(f"Motor speeds: M1={self.zkb1}, M2={self.zkb2}")
        self.stop()
    def backward(self, len):
        ed = time.time() + len / 13.5
        self.PIDcm[0].clear()
        self.PIDcm[1].clear()
        while time.time() < ed:
            # speed = self.board.get_encoder_speed(self.board.ALL)
            # self.board.motor_movement([self.board.M1], self.board.CW, self.PIDcm[0].compute(self.move_speed, speed[0]))
            # self.board.motor_movement([self.board.M2], self.board.CCW, self.PIDcm[1].compute(self.move_speed, speed[1]))
            self.board.motor_movement([self.board.M1], self.board.CW, 80)
            self.board.motor_movement([self.board.M2], self.board.CCW, 80)
        self.stop()
    def left(self, tm):
        ed = time.time() + tm
        self.PIDcm[0].clear()
        self.PIDcm[1].clear()
        while time.time() < ed:
            speed = self.board.get_encoder_speed(self.board.ALL)
            self.board.motor_movement([self.board.M1], self.board.CCW, 80)
            self.board.motor_movement([self.board.M2], self.board.CCW, 80)
        self.stop()
    def right(self, tm):
        ed = time.time() + tm
        self.PIDcm[0].clear()
        self.PIDcm[1].clear()
        while time.time() < ed:
            speed = self.board.get_encoder_speed(self.board.ALL)
            self.board.motor_movement([self.board.M1], self.board.CW, 80)
            self.board.motor_movement([self.board.M2], self.board.CW, 80)
        self.stop()

if __name__ == '__main__':
