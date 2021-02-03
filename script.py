import os
import pyautogui
import pywinauto
from pywinauto import application
from pywinauto.findwindows import WindowAmbiguousError, WindowNotFoundError
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
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

def end_teams_call():
    pyautogui.hotkey('ctrl' 'shift', 'b')

def volume_up():
    pyautogui.press('volumeup')

def volume_down():
    pyautogui.press('volumedown')

def set_volume_discord_up():
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        if session.Process and session.Process.name() == "Discord.exe":
            print("volume.GetMasterVolume(): %s" % volume.GetMasterVolume())
            volume_up_rate = volume.GetMasterVolume() + 0.05
            if volume_up_rate > 1:
                volume_up_rate = 1
            volume.SetMasterVolume(volume_up_rate, None)

def set_volume_discord_down():
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        if session.Process and session.Process.name() == "Discord.exe":
            print("volume.GetMasterVolume(): %s" % volume.GetMasterVolume())
            volume_up_rate = volume.GetMasterVolume() - 0.05
            if volume_up_rate < 0:
                volume_up_rate = 0
            volume.SetMasterVolume(volume_up_rate, None)

def set_volume_teams_down():
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        if session.Process and session.Process.name() == "Teams.exe":
            print("volume.GetMasterVolume(): %s" % volume.GetMasterVolume())
            volume_up_rate = volume.GetMasterVolume() - 0.05
            if volume_up_rate < 0:
                volume_up_rate = 0
            volume.SetMasterVolume(volume_up_rate, None)

def set_volume_teams_up():
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        if session.Process and session.Process.name() == "Teams.exe":
            print("volume.GetMasterVolume(): %s" % volume.GetMasterVolume())
            volume_up_rate = volume.GetMasterVolume() + 0.05
            if volume_up_rate > 1:
                volume_up_rate = 1
            volume.SetMasterVolume(volume_up_rate, None)

def main():
    app_teams = application.Application()
    app_teams_title = "Teams"
    app_discord = application.Application()
    app_discord_title = "Discord"
    try:
        app_teams.connect(title_re=app_teams_title)
        
        #Acces app_teams's window object
        app_teams_dialog = app_teams.window()
    except(WindowNotFoundError):
        print("Window: %s not Found" % app_teams_title)
    except(WindowAmbiguousError):
        print("There are to many %s windows found" % app_teams_title)
    
    try:
        app_discord.connect(title_re=app_discord_title)

        # Access app's window object
        app_discord_dialog = app_discord.window()
    except(WindowNotFoundError):
        print("Window: %s not Found" % app_discord_title)
    except(WindowAmbiguousError):
        print("There are to many %s windows found" % app_discord_title)

    #kurzer Test
    app_teams_dialog.set_focus()
    pyautogui.hotkey('ctrl', '1')
    time.sleep(2)
    pyautogui.hotkey('ctrl', '2')
    app_discord_dialog.set_focus()
    noSound_discord()
    time.sleep(2)
    noSound_discord()
    app_teams_dialog.set_focus()
        

try:
    # main()
    set_volume_teams_up()
except Exception as execption:
    print(execption)