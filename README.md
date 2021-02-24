# video conference automation
![video conference automation](/images/header.png)

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Generic badge](https://img.shields.io/badge/Made%20with-MicroPython-1f425f.svg)](http://docs.micropython.org/en/latest/)
[![Generic badge](https://img.shields.io/badge/Status-in%20progress-orange.svg)]()
[![GitHub license](https://img.shields.io/github/license/Naereen/StrapDown.js.svg)](https://github.com/hehimself/video-conference-automation/blob/main/LICENSE)

> You know that... your sitting in your MS Teams class but would much rather talk to your friends or classmates over Discord. Thats just one example where this automation tool with the Raspberry Pico and the Pimoroni RGB Keypad could be helpfull.

Inspired by products like the Elgatoo StreamDeck, here is the better and cheaper solution.

## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)
* [Features](#features)
* [Contact](#contact)

## General info
The Pico has a serial connection to the PC over USB. The Pico sends the pushed buttons as numbers to the PC and the `script.py` than taked the action. 

![pimoroni rgb keypad](https://cdn.shopify.com/s/files/1/0174/1800/products/pico-addons-2_1024x1024.jpg?v=1611177905)

## Technologies
### Hardware
* [Raspberry Pico](https://www.raspberrypi.org/documentation/pico/getting-started/)
* [Pimoroni RGB keypad Base](https://shop.pimoroni.com/products/pico-rgb-keypad-base)
### Libarys
* [PyAutoGUI](https://pyautogui.readthedocs.io/en/latest/) - used for hotkeys and screen analysis
* [pywinauto](https://pywinauto.readthedocs.io/en/latest/contents.html) - used to solve the active-window-problem
* [pycaw](https://github.com/AndreMiras/pycaw)  - used to control the volume
* [pico-rgbkeypad](https://github.com/martinohanlon/pico-rgbkeypad) - used to control the Pimoroni RGB keypad base from [@martinohanlon](https://github.com/martinohanlon/pico-rgbkeypad)

## Setup
install the requirements with:
```
$ pip install -r requirements.txt
```
Run the `pico-code.py` on your Pico.
Run the `script.py` on your PC.

## Code Examples
Show examples of usage:
`def mute_discord():`

code example:
```python
def mute_discord():
```
That's an example for one of the buttons:
```python
if key_4.is_pressed():
    key_4.color = (10,0,255)
    print(4)
    while key_4.is_pressed():
        time.sleep(0.1)
    key_4.color = (1, 0, 64)
```
## Features
General functions
* mute/unmute Discord and Teams
* the win-focus is always set to the right programm (important for keyboard shortcuts)
* control the general Volume
* control the volume of Discord or Teams

special features:
* "startup" automation
* "goodby" automation
* **"switch" automation**

| Automation         	| Description                                                                                                    	|
|--------------------	|----------------------------------------------------------------------------------------------------------------	|
| "startup" function 	| just one click and your whole home-schooling/gaming setup is ready, eveything is done for you automatically     	|
| "goodby" function  	| with just one click you leave the meeting, close Teams, go to Discord and you're ready for gaming.              	|
| "switch" function  	| you've got asked something by the teacher and have to switch very quickly bewteen Discord and Teams. or around 	|


## Contact
Created by [@hehimself](https://github.com/hehimself) - feel free to contact me!
