"""Normal boot: firmware owns storage. Maintenance: host owns CIRCUITPY."""

import storage
import usb_cdc
import usb_hid
import usb_midi
import microcontroller

maintenance = microcontroller.nvm[0] == 1
microcontroller.nvm[0] = 0
usb_midi.disable()
if maintenance:
    usb_hid.disable()
    usb_cdc.enable(console=True, data=False)
else:
    storage.disable_usb_drive()
    storage.remount("/", readonly=False)
    usb_cdc.enable(console=True, data=True)
    usb_hid.enable((usb_hid.Device.KEYBOARD, usb_hid.Device.CONSUMER_CONTROL))
