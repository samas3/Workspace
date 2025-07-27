from utils import util
from hardware import motor_control
import threading
import time
from PIL import Image, ImageDraw, ImageFont
import os
from services import yolo
import random
control = motor_control.MotorController()
def motor():
    while True:
        dist = util.get_distance_cm()
        print(dist)
        time.sleep(1)
        # p = util.get_battery()[3]
        # print('Battery:', p)
        # img = Image.new('RGB', (240, 240), color='black')
        # draw = ImageDraw.Draw(img)
        # font = ImageFont.load_default()
        # battery_color = 'red' if p < 20 else 'yellow' if p < 50 else 'green'
        # draw.text((20, 110), f"Battery: {p:.1f}%", font=font, fill=battery_color)
        # img = img.rotate(270)
        # util.display_img(img)
        DIST = 20
        if dist < DIST:
            if random.random() < 0.5:
                while dist < DIST:
                    dist = util.get_distance_cm()
                    control.left(0.05)
            else:
                while dist < DIST:
                    dist = util.get_distance_cm()
                    control.right(0.05)
        # else:
        #     control.forward(5)
        #     print('forward')
def serve():
    os.system('python3 server/server.py &')
def main():
    m = threading.Thread(target=motor, daemon=True)
    m.start()
    s = threading.Thread(target=serve, daemon=True)
    s.start()
    # while True:
    #     pass
    yolo.main()
if __name__ == "__main__":
    main()