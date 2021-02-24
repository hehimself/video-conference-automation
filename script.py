import os
import serial
import pyautogui
import pywinauto
from pywinauto import application
from pywinauto.findwindows import WindowAmbiguousError, WindowNotFoundError
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
import time
from time import sleep
from datetime import datetime

try:
    s = serial.Serial('COM6')
except serial.serialutil.SerialException:
    exit("Serieller Port nicht angeschlossen")

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
    pyautogui.hotkey('ctrl', 'shift', 'm')

def noSound_discord():
    pyautogui.hotkey('ctrl', 'shift', 'd')

def mute_ms_teams():
    pyautogui.hotkey('ctrl', 'shift', 'm')

def end_teams_call():
    pyautogui.hotkey('ctrl', 'shift', 'b')

def teams_raise_hand():
    pyautogui.hotkey('ctrl', 'shift', 'k')

#Funktionen ohne .set_focus() zuvor nötig
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

def get_serial():
    serial_message = s.readline()
    decoded_bytes = float(serial_message[0:len(serial_message)-2].decode("utf-8"))
    return decoded_bytes

def main(command):
    if command == 1:
        pass
    elif command == 2:
        volume_up()
    elif command == 3:
        set_volume_discord_up()
    elif command == 4:
        set_volume_teams_up()
    elif command == 5:
        pass
    elif command == 6:
        volume_down()
    elif command == 7:
        set_volume_discord_down()
    elif command == 8:
        set_volume_teams_down()
    elif command == 9:
        app_teams_dialog.set_focus()
        teams_raise_hand()
    elif command == 10:
        pass
    elif command == 11:
        pass
    elif command == 12:
        pass
    elif command == 13:
        app_teams_dialog.set_focus()
        mute_ms_teams()
    elif command == 14:
        app_discord_dialog.set_focus()
        mute_discord()
    elif command == 15:
        app_discord_dialog.set_focus()
        noSound_discord()
    elif command == 16:
        app_teams_dialog.set_focus()
        mute_ms_teams()
        app_discord_dialog.set_focus()
        mute_discord()
    else:
        print("falscher command")   

try:
    print("Programm gestartet")
    while True:
        command = get_serial()
        main(command)
except Exception as execption:
    s.close()
    print(execption)