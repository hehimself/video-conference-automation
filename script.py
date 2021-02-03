import os
import pyautogui
import pywinauto
from pywinauto import application
from pywinauto.findwindows import WindowAmbiguousError, WindowNotFoundError
import time
from time import sleep
from datetime import datetime

def open_ms_teams():
    os.startfile("C:/Users/marvin/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Microsoft Teams")
    #Teams
    sleep(3)
    teams = pyautogui.locateCenterOnScreen("images/teams_button.PNG")
    pyautogui.moveTo(teams)
    pyautogui.click()
    sleep(1)

def open_discord():
    os.startfile("C:/Users/marvin/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Discord Inc/Discord")
    sleep(4)
    #search Discord-Server
    server = pyautogui.locateCenterOnScreen("images/discord_gruppe.PNG")
    pyautogui.moveTo(server)
    pyautogui.click()
    pyautogui.hotkey('ctrl', 'shift', 'm')
    #select Channel
    kanal = pyautogui.locateCenterOnScreen("images/allgemein_kanal.PNG")
    pyautogui.moveTo(kanal)
    pyautogui.click()

def mute_discord():
    sleep(5)
    # discord = pyautogui.locateCenterOnScreen("images/discord.PNG")
    # pyautogui.moveTo(discord)
    # pyautogui.click
    pyautogui.hotkey('ctrl', 'shift', 'm')

def noSound_discord():
    pyautogui.hotkey('ctrl', 'shift', 'd')

def mute_ms_teams():
    pyautogui.hotkey('ctrl' 'shift', 'm')

def test_pywinauto():
    app = application.Application()
    app_title = "Teams"
    
    try:
        app.connect(title_re=app_title)
        
        #Acces app's window object
        app_dialog = app.window()
        
        # app_dialog.minimize()
        # app_dialog.restore()
        app_dialog.set_focus()
        pyautogui.hotkey('ctrl', '1')
        time.sleep(2)
        pyautogui.hotkey('ctrl', '2')

    except(WindowNotFoundError):
        print("Window: %s not Found" % app_title)
    except(WindowAmbiguousError):
        print("There are to many %s windows found" % app_title)
        

try:
    test_pywinauto()
    #open_ms_teams()
    #open_discord()
    #mute_discord()
except Exception as execption:
    print(execption)