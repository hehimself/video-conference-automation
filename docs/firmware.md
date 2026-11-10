# Firmware setup and recovery

This bundle targets the original RP2040 Raspberry Pi Pico and Pimoroni RGB Keypad
Base. CircuitPython is pinned to **10.3.1**, Adafruit HID to **6.1.4**. Downloads come
from the official CircuitPython server and Adafruit repository. The bundle includes
source URLs, hashes and upstream license text in its manifest.

## First installation

1. Install the desktop development environment described in the README.
2. Build the complete bundle: `python tools/build_firmware.py`.
3. Connect the existing CIRCUITPY device. Identify its **console** serial port.
4. Back up and enter its firmware bootloader:

   ```sh
   keypad-firmware --mount /Volumes/CIRCUITPY --console /dev/cu.usbmodem14301 \
     --backup-dir /path/to/private/backups --enter-bootloader
   ```

5. Copy `build/firmware-bundle/circuitpython-10.3.1-pico.uf2` to the newly mounted
   `RPI-RP2` drive. If automatic entry fails, unplug the Pico and reconnect while
   holding its BOOTSEL button.
6. Once CIRCUITPY returns, run the same command **without** `--enter-bootloader`.
   The installer verifies the board, makes another backup, stops autoreload,
   installs shared modules and the firmware, verifies copied entry points and
   reboots. Existing saved Studio profiles are retained; a first install starts
   with an empty profile.
7. Open Keypad Studio. It automatically connects to the DATA port. First use
   Learn/diagnostic mode and press each physical key to verify orientation. Then
   choose a profile, target OS, and Save to Pico.

On Windows, replace the mount and console with the appropriate drive and COM port,
for example `--mount E:/ --console COM7`. Windows and macOS assign different port
names; the console and DATA ports must not be confused.

## Normal storage ownership

Normal boot hides CIRCUITPY and gives the firmware exclusive write access. USB
keyboard/media, DATA and debug console remain available; USB MIDI is disabled.
Only Save to Pico writes profile flash. Preview and animation frames do not.

## Update installed firmware

The protocol's `maintenance` command releases HID keys and reboots into maintenance
mode. CIRCUITPY reappears, HID is disabled, and actions stop. Install updated files,
then unplug/reconnect to return to normal mode. The desktop setup utility can also
be used after entering maintenance. Maintenance is a one-boot flag.

## Recovery

If firmware does not boot, hold BOOTSEL while reconnecting. The RP2040's ROM
bootloader remains available. Copy the pinned UF2, enter CircuitPython safe mode
if necessary, restore your private backup or reinstall Studio, and reconnect.
Restoring older saved device code may also require its original CircuitPython
version, recorded in the backup's `boot_out.txt`.

Backups can contain text-entry secrets and personal paths. They are private local
files and must not be committed to the repository. The application starter layouts
contain neither the original text-entry literal nor personal script paths.
