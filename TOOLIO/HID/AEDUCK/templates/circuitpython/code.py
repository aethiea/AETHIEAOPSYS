import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

kbd = Keyboard(usb_hid.devices)

time.sleep(2)

kbd.press(Keycode.CONTROL, Keycode.ALT, Keycode.T)
kbd.release_all()

time.sleep(1)

print("AEDUCK hello_aethiea payload loaded")
