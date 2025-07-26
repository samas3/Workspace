from utils import util
from hardware import motor_control
import threading
import time
from PIL import Image, ImageDraw, ImageFont
import os
from server import server
from services import yolo
control = motor_control.MotorController()
def motor():
    while True:
        print(util.get_cpu_temp(), util.get_battery()[3])
        dist = util.get_distance_cm()
        print(dist)
        time.sleep(1)
        # p = util.get_battery()[3]
        # img = Image.new('RGB', (240, 240), color='black')
        # draw = ImageDraw.Draw(img)
        # font = ImageFont.load_default()
        # battery_color = 'red' if p < 20 else 'yellow' if p < 50 else 'green'
        # draw.text((20, 110), f"Battery: {p:.1f}%", font=font, fill=battery_color)
        # img = img.rotate(270)
        # util.display_img(img)

        # if 30 < dist < 100:
        #     control.right(0.3)
        #     print('right')
        # else:
        #     control.forward(5)
        #     print('forward')
def serve():
    # server.main()
    os.system('python3 server/server.py &')
def main():
    m = threading.Thread(target=motor, daemon=True)
    m.start()
    s = threading.Thread(target=serve, daemon=True)
    s.start()
    # v = threading.Thread(target=yolo.main, daemon=True)
    # v.start()
    # while True:
    #     pass
    yolo.main()
if __name__ == "__main__":
    main()