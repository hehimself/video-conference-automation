import os
import pyautogui
import time
from time import sleep
from datetime import datetime

def open_ms_teams():
    os.startfile("C:\Users\marvin\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Microsoft Teams")

try:
    pass
except Exception as execption:
    print(execption)