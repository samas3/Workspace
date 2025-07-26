import time
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add parent directory to sys.path to allow lib to be imported correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from lib.DFRobot_RaspberryPi_DC_Motor import DFRobot_DC_Motor_IIC as Board
except ImportError:
    logging.error("Could not import DFRobot_DC_Motor_IIC. Make sure the 'lib' directory is correctly set up.")
    sys.exit(1)

class PIDcontrolMove:
    def __init__(self, kp=0.0, ki=0.1, kd=0.05):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.last_error = 0
        self.integral = 0
        # Add integral wind-up protection (anti-windup)
        self.integral_max = 200 # Max value for integral term to prevent excessive build-up
        self.integral_min = -200 # Min value for integral term

    def compute(self, setpoint, measured_value):
        error = setpoint - measured_value
        self.integral += error
        # Apply integral wind-up protection
        self.integral = max(self.integral_min, min(self.integral, self.integral_max))

        derivative = error - self.last_error
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        self.last_error = error
        logging.debug(f"PID - Setpoint: {setpoint:.2f}; Measured: {measured_value:.2f}; Error: {error:.2f}; Output: {output:.2f}")
        return output

    def clear(self):
        self.integral = 0
        self.last_error = 0
        logging.info("PID controller state cleared.")

class MotorController:
    def __init__(self):
        self.board = Board(1, 0x10)
        if self.board.begin() != self.board.STA_OK:
            logging.error("Board begin fail! Please check your board connection and address.")
            sys.exit(1)
        else:
            logging.info("Board begin success.")

        self.board.set_encoder_enable(self.board.ALL)
        # Verify the reduction ratio. A value of 43 seems common for some motors.
        self.board.set_encoder_reduction_ratio(self.board.ALL, 43)
        self.board.set_moter_pwm_frequency(1000) # 1000Hz is a good frequency

        self.move_speed = 100 # Target encoder speed (magnitude)
        # Initialize PID controllers for M1 and M2
        # You might need different PID gains for each motor if they are significantly different
        self.PIDcm = [PIDcontrolMove(), PIDcontrolMove()]
        
        # Initial PWM values. These will be adjusted by PID.
        # Start with a value that typically gets the motors moving.
        self.motor_pwm = [80, 80] # [PWM for M1, PWM for M2]

    def stop(self):
        self.board.motor_stop(self.board.ALL)
        logging.info("All motors stopped.")

    def get_sign(self, speed):
        """Returns the sign of the speed (+1 for positive, -1 for negative, 0 for zero)."""
        if speed == 0:
            return 1
        return abs(speed) / speed

    def PIDctrlUpdate(self, setpoint_magnitude):
        """
        Updates motor PWM based on PID control for both motors.
        The setpoint_magnitude is the desired absolute encoder speed.
        """
        speeds = self.board.get_encoder_speed(self.board.ALL)
        logging.info(f"Current Encoder speeds: M1={speeds[0]:.2f}, M2={speeds[1]:.2f}")

        # Determine the setpoint for each motor based on its commanded direction
        # For M1 (forward), setpoint should be positive
        # For M2 (backward for straight movement), setpoint should be negative
        setpoint_m1 = setpoint_magnitude
        setpoint_m2 = -setpoint_magnitude # M2 moves in the opposite direction for straight forward movement

        # Compute PID output for each motor
        output_m1 = self.PIDcm[0].compute(setpoint_m1 * get_sign(speeds[0]), speeds[0])
        output_m2 = self.PIDcm[1].compute(setpoint_m2 * get_sign(speeds[1]), speeds[1])

        # Adjust motor_pwm based on PID output
        # The PID output is an adjustment, so we add it to the current PWM
        self.motor_pwm[0] += output_m1
        self.motor_pwm[1] += output_m2

        # Clamp PWM values to a valid range (e.g., 0-100 or a custom effective range)
        # Assuming 60-100 is your effective working range for these motors to move.
        self.motor_pwm[0] = max(60, min(self.motor_pwm[0], 100))
        self.motor_pwm[1] = max(60, min(self.motor_pwm[1], 100))
        
        logging.info(f"Updated Motor PWM: M1={self.motor_pwm[0]:.2f}, M2={self.motor_pwm[1]:.2f}")

    def forward(self, length_cm):
        """
        Moves the robot forward for a specified length.
        
        Args:
            length_cm (float): The distance to move in centimeters.
        """
        # Approximate conversion: 13.5 cm/second at move_speed 100
        # Adjust this constant based on your robot's actual performance
        duration = length_cm / 13.5 
        
        logging.info(f"Moving forward for {length_cm} cm (approx. {duration:.2f} seconds).")
        
        self.PIDcm[0].clear()
        self.PIDcm[1].clear()
        # Reset motor_pwm to a good starting value for the movement
        self.motor_pwm = [80, 80] 

        start_time = time.time()
        while time.time() - start_time < duration:
            # For forward, M1 CW and M2 CCW
            self.board.motor_movement([self.board.M1], self.board.CW, int(self.motor_pwm[0]))
            self.board.motor_movement([self.board.M2], self.board.CCW, int(self.motor_pwm[1]))
            
            self.PIDctrlUpdate(self.move_speed) # Pass the magnitude of the desired speed
            time.sleep(0.05) # Small delay to allow encoder readings and prevent busy-waiting
        self.stop()

    def backward(self, length_cm):
        """
        Moves the robot backward for a specified length.
        
        Args:
            length_cm (float): The distance to move in centimeters.
        """
        duration = length_cm / 13.5 # Same approximation as forward
        
        logging.info(f"Moving backward for {length_cm} cm (approx. {duration:.2f} seconds).")

        self.PIDcm[0].clear()
        self.PIDcm[1].clear()
        # Reset motor_pwm to a good starting value for the movement
        self.motor_pwm = [80, 80] 

        start_time = time.time()
        while time.time() - start_time < duration:
            # For backward, M1 CCW and M2 CW
            self.board.motor_movement([self.board.M1], self.board.CCW, int(self.motor_pwm[0]))
            self.board.motor_movement([self.board.M2], self.board.CW, int(self.motor_pwm[1]))
            
            # For backward, the desired encoder speeds are now negative for M1 and positive for M2
            # However, PIDctrlUpdate is designed to take the magnitude of the speed
            # and internally determine the setpoint sign based on the motor's role in straight movement.
            # So, we pass self.move_speed as the magnitude.
            self.PIDctrlUpdate(self.move_speed)
            time.sleep(0.05)
        self.stop()

    def turn_left(self, deg):
        logging.warning("Turn left function not implemented yet.")
        pass

    def turn_right(self, deg):
        logging.warning("Turn right function not implemented yet.")
        pass

if __name__ == '__main__':
    motor = MotorController()
    try:
        motor.forward(135)
        # You can add more movements here for testing, e.g.:
        # time.sleep(2)
        # motor.backward(50)
    except KeyboardInterrupt:
        logging.info("Program interrupted by user. Stopping motors.")
    finally:
        motor.stop()