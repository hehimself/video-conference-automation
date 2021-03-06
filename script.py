import os
import time
import serial
import colorama
import pyautogui
import playsound
import pywinauto
from threading import Thread
from termcolor import colored
from pywinauto import application
from pywinauto.findwindows import WindowAmbiguousError, WindowNotFoundError, ElementNotFoundError
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from datetime import datetime

colorama.init()

try:
    s = serial.Serial('COM6')
except serial.serialutil.SerialException:
    exit("Serieller Port nicht angeschlossen")


def open_ms_teams():
    os.startfile("C:/Users/marvin/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Microsoft Teams")
    #Teams
    time.sleep(10)
    teams = pyautogui.locateCenterOnScreen("images/teams_button.PNG")
    pyautogui.moveTo(teams)
    pyautogui.click()
    time.sleep(1)

def open_discord():
    os.startfile("C:/Users/marvin/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Discord Inc/Discord")
    time.sleep(10)
    #search Discord-Server
    server = pyautogui.locateCenterOnScreen("images/discord_gruppe.PNG")
    pyautogui.moveTo(server)
    pyautogui.click()
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

def sound():
    playsound.playsound("jarvis_funny.mp3")

def get_serial():
    try:
        serial_message = s.readline()
    except KeyboardInterrupt:
        exit(colored("programm ended", "red"))
    except serial.SerialException:
        print("Serial Exception")
    try:
        decoded_bytes = float(serial_message[0:len(serial_message)-2].decode("utf-8"))
    except:
        exit("Serial Error")
    return decoded_bytes

app_teams = application.Application()
app_teams_title = "Besprechung in „Technik (Dr)“"
for attempts in range(2):
    try:
        app_teams.connect(title_re="Teams")
        #Acces app_teams's window object
        app_teams_dialog = app_teams.window()
    except(WindowNotFoundError):
        print("Window: %s not Found" % app_teams_title)
    except(WindowAmbiguousError):
        print("There are to many %s windows found" % app_teams_title)
    except(ElementNotFoundError):
        open_ms_teams()
    else:
        break
else:
    raise ElementNotFoundError


app_discord = application.Application()
app_discord_title = "#Allgemein - Discord"
for attempts in range(2):
    try:
        app_discord.connect(title_re=app_discord_title)

        # Access app's window object
        app_discord_dialog = app_discord.window()
    except(WindowNotFoundError):
        print("Window: %s not Found" % app_discord_title)
    except(WindowAmbiguousError):
        print("There are to many %s windows found" % app_discord_title)
    except(ElementNotFoundError):
        open_discord()
    else:
        break
else:
    raise ElementNotFoundError

def main(command):
    if command == 1:
        T = Thread(target=sound) # create thread
        T.start()
        time.sleep(4)
        app_teams_dialog.set_focus()
        app_discord_dialog.set_focus()
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
    print(colored("VIDEO CONFERENCE AUTOMATION", "green", attrs=['bold']))
    while True:
        command = get_serial()
        main(command)
except KeyboardInterrupt:
    s.close()
    exit(colored("programm ended", "red"))
except pywinauto.findwindows.ElementNotFoundError:
    exit(colored("Error - ElementNotFoundError", "red"))