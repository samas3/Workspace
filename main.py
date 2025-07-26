from utils import util
from hardware import motor_control
import threading
import time
from PIL import Image, ImageDraw, ImageFont
import os
def motor():
    while True:
        dist = util.get_distance_cm()
        print(dist)
        time.sleep(1)
        p = util.get_battery()[3]
        print(p)
        img = Image.new('RGB', (240, 240), color='black')
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        battery_color = 'red' if p < 20 else 'yellow' if p < 50 else 'green'
        draw.text((20, 110), f"Battery: {p:.1f}%", font=font, fill=battery_color)
        img = img.rotate(270)
        util.display_img(img)
        # if dist < 10:
        #     motor_control.backward(10)
        #     motor_control.right(45)
        # else:
        #     motor_control.forward(5)
m = threading.Thread(target=motor)
m.start()
os.system('python3 server/server.py &')