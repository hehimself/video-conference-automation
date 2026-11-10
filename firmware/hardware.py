"""Pimoroni RGB Keypad Base: raw index = 4*y+x, matching the original driver."""

import board
import busio
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.consumer_control import ConsumerControl


class Hardware:
    def __init__(self):
        self.i2c = busio.I2C(board.GP5, board.GP4, frequency=400000)
        while not self.i2c.try_lock():
            pass
        self.spi = busio.SPI(board.GP18, MOSI=board.GP19)
        while not self.spi.try_lock():
            pass
        self.spi.configure(baudrate=4000000)
        self.cs = digitalio.DigitalInOut(board.GP17)
        self.cs.direction = digitalio.Direction.OUTPUT
        self.cs.value = True
        self.keyboard = Keyboard(usb_hid.devices)
        self.consumer = ConsumerControl(usb_hid.devices)
        self.switches = bytearray(2)
        self.address = bytearray([0])
        self.leds = bytearray(72)
        for i in range(4):
            self.leds[68 + i] = 255

    def read_keys(self):
        self.i2c.writeto_then_readfrom(0x20, self.address, self.switches)
        bits = self.switches[0] | self.switches[1] << 8
        return [not bits & (1 << i) for i in range(16)]

    def write_leds(self, colors):
        for i, (r, g, b) in enumerate(colors):
            offset = 4 + i * 4
            self.leds[offset] = 255
            self.leds[offset + 1] = b
            self.leds[offset + 2] = g
            self.leds[offset + 3] = r
        self.cs.value = False
        self.spi.write(self.leds)
        self.cs.value = True

    def tap(self, codes):
        self.keyboard.send(*codes)

    def media(self, code):
        self.consumer.send(code)

    def release_all(self):
        self.keyboard.release_all()
        self.consumer.release()

    def maintenance(self):
        import microcontroller

        microcontroller.nvm[0] = 1
        microcontroller.reset()
