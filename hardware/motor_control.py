import time
import logging
import sys
import os

# 假设DFRobot库在父目录的lib文件夹下
# 添加父目录到 sys.path，使得 lib 可以被正确导入
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from lib.DFRobot_RaspberryPi_DC_Motor import DFRobot_DC_Motor_IIC as Board

# --- Mock Board for Testing without Hardware ---
# 如果您没有硬件环境，可以使用下面的模拟类来测试代码逻辑
class MockBoard:
    M1, M2, ALL = 0, 1, 2
    CW, CCW = 1, 2
    STA_OK = 0

    def __init__(self, *args, **kwargs):
        self._speeds = [0.0, 0.0]
        self._duty = [0, 0]

    def begin(self):
        print("Mock Board Initialized")
        return self.STA_OK

    def set_encoder_enable(self, *args): pass
    def set_encoder_disable(self, *args): pass
    def set_encoder_reduction_ratio(self, *args, **kwargs): pass
    def set_moter_pwm_frequency(self, *args): pass
    def motor_stop(self, *args): print("Motors Stopped")
    
    def motor_movement(self, motors, direction, duty):
        # 简单模拟占空比与速度的关系
        for m in motors:
            self._duty[m] = duty
            # 模拟电机响应，速度不会立即达到目标
            # 这里用一个简化模型，并加入一点随机噪声
            target_speed_from_duty = duty * 0.85 
            if m == 1: # 假设M2电机稍弱一些
                target_speed_from_duty *= 0.95
            self._speeds[m] += (target_speed_from_duty - self._speeds[m]) * 0.5
            
    def get_encoder_speed(self, *args):
        # 返回模拟的速度
        return self._speeds

# 使用实际的板卡或者模拟板卡
# board = Board(1, 0x10)
board = MockBoard(1, 0x10) 
# --- End of Mock Board ---


class PIDController:
    """一个包含标准时间增量(dt)计算的PID控制器。"""
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral = 0
        self.last_error = 0
        self.last_time = time.time()

    def compute(self, error):
        """根据误差计算PID调整值。"""
        current_time = time.time()
        dt = current_time - self.last_time

        if dt <= 0:  # 避免除以零
            return 0

        # 比例项
        proportional = self.kp * error

        # 积分项 (包含抗积分饱和的隐含逻辑，如果需要显式处理，可以在此添加)
        self.integral += error * dt
        integral_term = self.ki * self.integral

        # 微分项
        derivative = self.kd * (error - self.last_error) / dt

        # 更新状态
        self.last_error = error
        self.last_time = current_time

        return proportional + integral_term + derivative

    def clear(self):
        """重置PID状态，用于新的独立运动。"""
        self.integral = 0
        self.last_error = 0
        self.last_time = time.time()


class MotorController:
    def __init__(self):
        self.board = board # 使用上面定义的全局board实例
        if self.board.begin() != self.board.STA_OK:
            raise IOError("Board initialization failed")
        print("Board begin success")

        # 初始化电机和编码器设置
        self.board.set_encoder_enable(self.board.ALL)
        self.board.set_encoder_reduction_ratio(self.board.ALL, 43)
        self.board.set_moter_pwm_frequency(1000)

        # PID 和电机控制参数
        self.pid = PIDController(kp=0.8, ki=0.05, kd=0.2)
        self.base_duty = 60      # 基础占空比
        self.max_duty = 100      # 最大占空比
        self.min_duty = 30       # 最小占空比
        self.target_speed = 50   # 目标转速(rpm)，主要用于参考和打印

    def stop(self):
        """停止所有电机并禁用编码器。"""
        self.board.motor_stop(self.board.ALL)
        self.board.set_encoder_disable(self.board.ALL)
        print("Movement finished and resources cleaned up.")

    def ramp_up(self, target_duty, duration=2):
        """缓慢加速到目标占空比，以减少启动时的冲击。"""
        print(f"Ramping up to {target_duty}% duty cycle...")
        step_delay = 0.1
        steps = int(duration / step_delay)
        if steps == 0: steps = 1
        
        for i in range(1, steps + 1):
            duty = int(target_duty * (i / steps))
            # 假设M1前进为CW，M2前进为CCW (根据机器人组装情况可能不同)
            self.board.motor_movement([self.board.M1], self.board.CW, duty)
            self.board.motor_movement([self.board.M2], self.board.CCW, duty)
            time.sleep(step_delay)

    def _move(self, duration_sec, direction='forward'):
        """
        核心运动控制函数，使用PID进行速度同步。
        :param duration_sec: 运动持续时间（秒）。
        :param direction: 'forward' 或 'backward'。
        """
        # 设置电机方向
        if direction == 'forward':
            m1_dir, m2_dir = self.board.CW, self.board.CCW
        elif direction == 'backward':
            m1_dir, m2_dir = self.board.CCW, self.board.CW
        else:
            return

        print(f"Starting {direction} movement for {duration_sec:.1f} seconds.")
        
        # 重置PID控制器并开始运动
        self.pid.clear()
        self.ramp_up(self.base_duty) # 缓慢加速到基础占空比

        start_time = time.time()
        last_print_time = start_time

        while time.time() - start_time < duration_sec:
            # 1. 获取当前电机转速
            speeds = self.board.get_encoder_speed(self.board.ALL)
            m1_speed, m2_speed = speeds[0], speeds[1]

            # 2. 计算速度差 (M1作为基准，M2需要匹配M1)
            # 目标是让 error -> 0
            speed_error = m1_speed - m2_speed

            # 3. 获取PID调整值
            adjustment = self.pid.compute(speed_error)

            # 4. 调整电机占空比
            m1_duty = self.base_duty
            # M2的速度需要根据误差进行调整
            m2_duty = self.base_duty - adjustment # 如果M2比M1快(error>0)，则减小M2功率

            # 5. 限制占空比在合理范围内
            m2_duty_clamped = max(self.min_duty, min(self.max_duty, m2_duty))

            # 6. 设置电机
            self.board.motor_movement([self.board.M1], m1_dir, int(m1_duty))
            self.board.motor_movement([self.board.M2], m2_dir, int(m2_duty_clamped))

            # 7. 定期打印状态
            if time.time() - last_print_time > 0.5:
                print(f"M1: {m1_speed:5.1f}rpm, M2: {m2_speed:5.1f}rpm, "
                      f"Err: {speed_error:5.1f}, Adj: {adjustment:5.1f}, M2 Duty: {m2_duty_clamped:.1f}")
                last_print_time = time.time()

            # 8. 控制循环频率
            time.sleep(0.05)

    def forward(self, distance_cm):
        """
        向前移动指定距离。
        需要预先测定速度和时间的关系。您的代码中使用13.5cm/s。
        """
        estimated_speed_cm_s = 13.5 
        duration = distance_cm / estimated_speed_cm_s
        self._move(duration, direction='forward')
        self.stop()

    def backward(self, distance_cm):
        """向后移动指定距离。"""
        estimated_speed_cm_s = 13.5
        duration = distance_cm / estimated_speed_cm_s
        self._move(duration, direction='backward')
        self.stop()

    def turn_left(self, deg):
        # 转向逻辑待实现
        pass

    def turn_right(self, deg):
        # 转向逻辑待实现
        pass

if __name__ == '__main__':
    try:
        motor = MotorController()
        motor.forward(135) # 向前移动135厘米
        # time.sleep(1)
        # motor.backward(135) # 向后移动135厘米
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 确保在程序退出时电机能停止
        board.motor_stop(board.ALL)
        print("Program finished.")