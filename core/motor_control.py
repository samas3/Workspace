import time
import logging
import sys
import os

# 添加父目录到 sys.path，使得 lib 可以被正确导入
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.DFRobot_RaspberryPi_DC_Motor import DFRobot_DC_Motor_IIC as Board

# 设置日志级别，方便调试
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PIDController:
    """
    一个用于电机速度控制的PID控制器类，包含时间间隔计算。
    """
    def __init__(self, kp, ki, kd):
        self.kp = kp        # 比例系数
        self.ki = ki        # 积分系数
        self.kd = kd        # 微分系数
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = time.time() # 记录上次计算时间

    def compute(self, setpoint, measured_value):
        """
        计算PID输出值。

        Args:
            setpoint (float): 目标设定值 (例如，目标转速)。
            measured_value (float): 当前测量值 (例如，实际转速)。

        Returns:
            float: PID控制器计算出的调整值。
        """
        current_time = time.time()
        dt = current_time - self.last_time

        if dt == 0: # 避免除以零
            return 0.0

        error = setpoint - measured_value

        # 比例项
        proportional = self.kp * error

        # 积分项 (包含抗积分饱和逻辑，但这里简化为直接累加)
        self.integral += error * dt
        integral = self.ki * self.integral

        # 微分项
        derivative = self.kd * (error - self.last_error) / dt

        # 计算总输出
        output = proportional + integral + derivative

        # 更新状态
        self.last_error = error
        self.last_time = current_time

        # logging.debug("Setpoint: %.2f, Measured: %.2f, Error: %.2f, P: %.2f, I: %.2f, D: %.2f, Output: %.2f" %
        #               (setpoint, measured_value, error, proportional, integral, derivative, output))
        return output

    def clear(self):
        """重置PID控制器状态。"""
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = time.time()

class MotorController:
    """
    控制两个电机运动的类。
    """
    def __init__(self):
        self.board = Board(1, 0x10) # 树莓派的I2C总线1，I2C地址0x10
        if self.board.begin() != self.board.STA_OK:
            logging.error("Board begin failed!")
            sys.exit(1) # 退出程序如果板卡初始化失败
        else:
            logging.info("Board begin success.")

        self.board.set_encoder_enable(self.board.ALL)
        self.board.set_encoder_reduction_ratio(self.board.ALL, 43)
        self.board.set_moter_pwm_frequency(1000)

        self.target_speed = 50 # 目标转速(rpm)
        self.base_duty = 60    # 基础占空比
        self.max_duty = 100    # 最大占空比
        self.min_duty = 30     # 最小占空比

        # 为M1和M2分别创建PID控制器，用于将各自电机稳定在 target_speed
        # Kp, Ki, Kd 参数需要根据实际电机特性进行调整
        self.pid_motor1 = PIDController(kp=0.8, ki=0.05, kd=0.2)
        self.pid_motor2 = PIDController(kp=0.8, ki=0.05, kd=0.2)

        # 差速PID控制器，用于M2匹配M1 (可选，如果两个电机特性差异大)
        # self.pid_differential = PIDController(kp=0.5, ki=0.01, kd=0.1)

        self.m1_current_duty = self.base_duty
        self.m2_current_duty = self.base_duty

        logging.info(f"MotorController initialized. Target speed: {self.target_speed} RPM.")

    def stop(self):
        """停止所有电机并禁用编码器。"""
        self.board.motor_stop(self.board.ALL)
        self.board.set_encoder_disable(self.board.ALL)
        logging.info("All motors stopped and encoders disabled.")

    def ramp_up(self, target_duty=60, duration=2):
        """
        缓慢加速到目标占空比。
        M1 CW, M2 CCW 表示向前运动。
        """
        logging.info("Ramping up motors...")
        step = 5
        for duty in range(0, target_duty + step, step):
            if duty > target_duty: # 确保不超过目标占空比
                duty = target_duty
            self.board.motor_movement([self.board.M1], self.board.CW, duty)
            self.board.motor_movement([self.board.M2], self.board.CCW, duty)
            time.sleep(duration / (target_duty / step)) # 调整sleep时间，使加速更平滑
            if duty == target_duty:
                break # 达到目标后退出

        self.m1_current_duty = target_duty
        self.m2_current_duty = target_duty
        logging.info(f"Ramp up complete. Current duty: M1={self.m1_current_duty}, M2={self.m2_current_duty}")


    def forward(self, duration_sec):
        """
        使两个电机向前运动指定时间，并使用PID控制转速。

        Args:
            duration_sec (float): 运动持续时间 (秒)。
        """
        logging.info(f"Starting forward movement for {duration_sec} seconds, target speed: {self.target_speed} RPM")

        # 重置PID控制器
        self.pid_motor1.clear()
        self.pid_motor2.clear()
        # self.pid_differential.clear() # 如果使用差速PID也需清空

        # 缓慢加速到基础占空比
        self.ramp_up(self.base_duty)

        start_time = time.time()
        last_print_time = start_time
        control_interval = 0.05 # PID控制循环间隔

        try:
            while time.time() - start_time < duration_sec:
                current_time = time.time()

                # 获取当前电机转速
                speeds = self.board.get_encoder_speed(self.board.ALL)
                m1_speed = speeds[0]
                m2_speed = speeds[1]

                # --- 独立PID控制 M1 转速 ---
                # 计算 M1 调整量
                # PID输出为调整量，加到当前占空比上
                m1_adjustment = self.pid_motor1.compute(self.target_speed, m1_speed)
                self.m1_current_duty += m1_adjustment

                # --- 独立PID控制 M2 转速 ---
                # 计算 M2 调整量
                m2_adjustment = self.pid_motor2.compute(self.target_speed, m2_speed)
                self.m2_current_duty += m2_adjustment

                # --- (可选) 差速PID调整 M2 以匹配 M1 ---
                # 如果需要M2严格跟随M1，可以使用以下差速PID
                # speed_error = m1_speed - m2_speed # M1作为基准，M2需要匹配M1
                # differential_adjustment = self.pid_differential.compute(0, speed_error) # 目标是速度差为0
                # self.m2_current_duty += differential_adjustment

                # 限制占空比在合理范围内
                self.m1_current_duty = max(self.min_duty, min(self.max_duty, self.m1_current_duty))
                self.m2_current_duty = max(self.min_duty, min(self.max_duty, self.m2_current_duty))

                # 设置电机运动
                # 注意：duty需要是整数
                self.board.motor_movement([self.board.M1], self.board.CW, int(self.m1_current_duty))
                self.board.motor_movement([self.board.M2], self.board.CCW, int(self.m2_current_duty))

                # 定期打印状态
                if current_time - last_print_time >= 0.5: # 每0.5秒打印一次
                    logging.info(f"M1: Speed={m1_speed:5.1f} RPM, Duty={self.m1_current_duty:5.1f}% | "
                                 f"M2: Speed={m2_speed:5.1f} RPM, Duty={self.m2_current_duty:5.1f}%")
                    last_print_time = current_time

                time.sleep(control_interval) # 控制循环频率

        except KeyboardInterrupt:
            logging.warning("Forward movement manually interrupted.")
        finally:
            self.stop()
            logging.info("Forward movement finished.")

    # 你可以继续实现backward, turn_left, turn_right等方法
    # 例如：
    def backward(self, duration_sec):
        logging.info(f"Starting backward movement for {duration_sec} seconds, target speed: {self.target_speed} RPM")
        self.pid_motor1.clear()
        self.pid_motor2.clear()
        self.m1_current_duty = self.base_duty
        self.m2_current_duty = self.base_duty
        start_time = time.time()
        last_print_time = start_time
        control_interval = 0.05

        try:
            while time.time() - start_time < duration_sec:
                current_time = time.time()
                speeds = self.board.get_encoder_speed(self.board.ALL)
                m1_speed = speeds[0]
                m2_speed = speeds[1]

                # 注意：后退时如果编码器返回的是负值，PID的setpoint和measured_value也应为负值
                # 或者将编码器读数取绝对值，然后根据方向设置PID的目标
                # 假设 get_encoder_speed 返回的是正值，且我们希望控制其绝对速度
                m1_adjustment = self.pid_motor1.compute(self.target_speed, abs(m1_speed))
                self.m1_current_duty += m1_adjustment

                m2_adjustment = self.pid_motor2.compute(self.target_speed, abs(m2_speed))
                self.m2_current_duty += m2_adjustment

                self.m1_current_duty = max(self.min_duty, min(self.max_duty, self.m1_current_duty))
                self.m2_current_duty = max(self.min_duty, min(self.max_duty, self.m2_current_duty))

                self.board.motor_movement([self.board.M1], self.board.CCW, int(self.m1_current_duty))
                self.board.motor_movement([self.board.M2], self.board.CW, int(self.m2_current_duty))

                if current_time - last_print_time >= 0.5:
                    logging.info(f"M1: Speed={m1_speed:5.1f} RPM, Duty={self.m1_current_duty:5.1f}% | "
                                 f"M2: Speed={m2_speed:5.1f} RPM, Duty={self.m2_current_duty:5.1f}%")
                    last_print_time = current_time
                time.sleep(control_interval)
        except KeyboardInterrupt:
            logging.warning("Backward movement manually interrupted.")
        finally:
            self.stop()
            logging.info("Backward movement finished.")


if __name__ == '__main__':
    motor_controller = MotorController()
    motor_controller.forward(10) # 车辆向前运动10秒
    # motor_controller.backward(10) # 车辆向后运动10秒