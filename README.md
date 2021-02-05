# video conference automation
![video conference automation](/images/header.PNG)

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Generic badge](https://img.shields.io/badge/Made%20with-MicroPython-1f425f.svg)](http://docs.micropython.org/en/latest/)
[![Generic badge](https://img.shields.io/badge/Status-in%20progress-orange.svg)]()
[![GitHub license](https://img.shields.io/github/license/Naereen/StrapDown.js.svg)](https://github.com/hehimself/video-conference-automation/blob/main/LICENSE)

> You know that... your sitting in your MS Teams class but would much rather talk to your friends ore classmates over Discord. Thats just one example where this automation tool with the Raspberry Pico and the Pimoroni RGB Keypad could be helpfull.

Inspired by products like the Elgatoo StreamDeck, here is the better and cheaper solution.

## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)
* [Features](#features)
* [Contact](#contact)

## General info
Add more general information about project. What the purpose of the project is? Motivation?



## Technologies
### Hardware
* [Raspberry Pico](https://www.raspberrypi.org/documentation/pico/getting-started/)
* [Pimoroni RGB keypad Base](https://shop.pimoroni.com/products/pico-rgb-keypad-base)
### Libarys
* [PyAutoGUI](https://pyautogui.readthedocs.io/en/latest/) - used for hotkeys and screen analysis
* [pywinauto](https://pywinauto.readthedocs.io/en/latest/contents.html) - used to solve the active-window-problem
* [pycaw](https://github.com/AndreMiras/pycaw)  - used to control the volume

## Setup
Describe how to install / setup your local environement / add link to demo version.

## Code Examples
Show examples of usage:
`def mute_discord():`

realsy code example:
```python
def mute_discord():
```

## Features
General functions
* mute/unmute Discord and Teams
* the win-focus is always set to the right programm (important for keyboard shortcuts)
* control the general Volume
* control the volume of Discord or Teams

special features:
* "startup" automation: just one click and your whole home-schooling/gaming setup is ready
* "goodby" automation: with one click you leave the meeting, close Teams, go to Discord, unmute Discord...ready for free Time
* **"switch" automation**: you've got asked someting by the teacher aan have to switch very quickly between Discord and Teams.


## Contact
Created by [@hehimself](https://github.com/hehimself) - feel free to contact me!