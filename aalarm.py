import binascii
import sys
import codecs

import Adafruit_PN532 as PN532
import Adafruit_GPIO.MCP230xx as MCP
import Adafruit_CharLCD as LCD
from time import sleep
import RPi.GPIO as GPIO

import threading
from collections import deque
import Adafruit_PN532 as PN532

import Adafruit_GPIO.MCP230xx as MCP
import Adafruit_CharLCD as LCD

from threading import Timer

from flask import Flask

import configparser

import requests
from requests.auth import HTTPBasicAuth

class LcdControl(object):
    address = 0x20
    lines = 16
    cols = 2
    gpio = None
    lcd = None
    currentMenu = None

    def __init__(self):
        self.gpio = MCP.MCP23008(self.address)
        self.lcd = LCD.Adafruit_CharLCD(1, 2, 3, 4, 5 , 6, self.lines, self.cols, gpio=self.gpio, backlight=7, invert_polarity=False)

    def display(self, message):
        print('LCD [%s]' % message)
        self.lcd.clear()
        self.lcd.message(message)

    def displayState(self, state, status):
        self.display('State [' + state + ']\n' + 'Status [' + status + ']')

    def displayMenu(self):
        self.display('Menu\nOptions')

    def menuButton(self, button):
        if not self.currentMenu:
            self.displayMenu()


class MenuControl(object):
    PIN_BT_SELECT = 26
    PIN_BT_UP = 19
    PIN_BT_DWN = 13

    def __init__(self, running, queue, lock):
        self.running = running
        self.queue = queue
        self.lock = lock

        GPIO.setup(self.PIN_BT_SELECT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.PIN_BT_SELECT, GPIO.FALLING, callback=self.callbackBtSelect, bouncetime=500)
        GPIO.setup(self.PIN_BT_UP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.PIN_BT_UP, GPIO.FALLING, callback=self.callbackBtUp, bouncetime=500)
        GPIO.setup(self.PIN_BT_DWN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.PIN_BT_DWN, GPIO.FALLING, callback=self.callbackBtDown, bouncetime=500)

    def callbackBtSelect(self, channel):
        with self.lock:
            self.queue.append('SELECT')

    def callbackBtUp(self, channel):
        with self.lock:
            self.queue.append('UP')

    def callbackBtDown(self, channel):
        with self.lock:
            self.queue.append('DOWN')

class Alarm(object):
    state = False
    dStatusAlarm = {0: 'nominal', 1: 'breach', 2: 'warning', 3: 'alert'}
    status = 0

    def toggleState(self):
        print('Toggle before [%s]' % self.state)
        self.state = not self.state
        print('Toggle after [%s]' % self.state)
        if not self.state:
            print('Online')
            self.status = 0
            callDomoticz(configDomoticzSceneLeaveUrl)
        else:
            print('Offline')
            callDomoticz(configDomoticzSceneEnterUrl)

    def setOnline(self):
        self.state = 1

    def setOffline(self):
        self.state = 0

    def sensorBreach(self):
        if self.state:
            if self.status == 0:
                self.status = 1;
            elif self.status == 1:
                self.status = 2;
            elif self.status == 2:
                self.status = 3;

    def currentState(self):
        if self.state:
            return 'online'
        else:
            return 'offline'

    def currentStatus(self):
        return self.dStatusAlarm[self.status]

class NfcReader(object):
    pn532 = None

    CS   = 18
    MOSI = 23
    MISO = 24
    SCLK = 25

    running = None
    queue = None
    lock = None


    def __init__(self, running, queue, lock):
        self.running = running
        self.queue = queue
        self.lock = lock

        self.pn532 = PN532.PN532(cs=self.CS, sclk=self.SCLK, mosi=self.MOSI, miso=self.MISO)
        self.pn532.begin()
        ic, ver, rev, support = self.pn532.get_firmware_version()
        print('Starting PN532 (firmware version: {0}.{1})'.format(ver, rev))
        self.pn532.SAM_configuration()

    def nfc_reader(self):
        while True:
            if not self.running:
                return

            uid = self.pn532.read_passive_target()

            if uid is None:
                continue

            #cardUid = bytes(uid)
            cardUid = binascii.hexlify(uid)
            with self.lock:
                self.queue.append(cardUid)
            sleep(1)

class GpioSensor(object):
    PIN_SENSOR_1 = 6
    PIN_SENSOR_2 = 5
    TIMEOUT_WARNING = 5
    TIMEOUT_ALERT = 10
    timerWarning = None
    timerAlert = None

    running = None
    queue = None
    lock = None

    def __init__(self, running, queue, lock):
        self.running = running
        self.queue = queue
        self.lock = lock
        GPIO.setup(self.PIN_SENSOR_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.PIN_SENSOR_1, GPIO.FALLING, callback=self.callbackSensor, bouncetime=500)
        GPIO.setup(self.PIN_SENSOR_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.PIN_SENSOR_2, GPIO.FALLING, callback=self.callbackSensor, bouncetime=500)

    def callbackSensor(self,channel):
        #alarm.sensorBreach()
        #lcdControl.displayState(alarm.currentState(), alarm.currentStatus())
        if not self.timerWarning:
            self.timerWarning = Timer(5,self.callbackEscalade,args=[channel, 'warning'])
            self.timerWarning.start()
            self.timerAlert = Timer(10,self.callbackEscalade,args=[channel, 'alert'])
            self.timerAlert.start()
            with self.lock:
                self .queue.append('SENSOR_BREACH')

    def callbackEscalade(self, channel, timerName):
        #alarm.sensorBreach()
        #lcdControl.displayState(alarm.currentState(), alarm.currentStatus())
        print('Escalade ' + timerName)
        if timerName == 'alert':
            self.timerWarning = None
            self.timerAlert = None

        #print('escalade sensor', channel)
        with self.lock:
            self.queue.append('SENSOR_ESCALADE')

    def stop(self):
        print('stop timers')

        if self.timerWarning is not None:
            print('stop warning')
            self.timerWarning.cancel()
        if self.timerAlert is not None:
            print('stop alert')
            self.timerAlert.cancel()

#Threading queues and locks
queue_sensors = deque()
lock_sensors = threading.Lock()

queue_nfc = deque()
lock_nfc = threading.Lock()

queue_buttons = deque()
lock_buttons = threading.Lock()

running = True

#ConfigParser
configParser = configparser.RawConfigParser()
configFilePath = r'config'
configParser.read(configFilePath)

configNfckeys = configParser.get('nfc-keys', 'keys')

validUid = {}
for key_name in configNfckeys.split(','):
    print('key [%s]' % key_name)
    key_value = configParser.get('nfc-keys', key_name)
    print('value [%s]' % key_value)
    validUid[key_name] = key_value

configDomoticzLogin = configParser.get('domoticz', 'login')
configDomoticzPwd = configParser.get('domoticz', 'password')

configDomoticzSceneLeaveUrl = configParser.get('domoticz', 'sceneLeave')
configDomoticzSceneEnterUrl = configParser.get('domoticz', 'sceneEnter')

#sceneEnter="http://192.168.0.23:8080/json.htm?type=command&param=switchscene&idx=8&switchcmd=On";
#scenePresenceOn="http://192.168.0.23:8080/json.htm?type=command&param=switchlight&idx=23&switchcmd=On";
#scenePresenceOff="http://192.168.0.23:8080/json.htm?type=command&param=switchlight&idx=23&switchcmd=Off";

def callDomoticz(url):
    print(print('call [%s]' % url))
    response = requests.get(url, auth=HTTPBasicAuth(configDomoticzLogin, configDomoticzPwd))
    print(response)

def main_loop():
    while True:
        if queue_buttons:
            with lock_buttons:
                button = queue_buttons.popleft()
                print('button ' + button)
                lcdControl.menuButton(button)

        if queue_sensors:
            with lock_sensors:
                sensor = queue_sensors.popleft()
                if (alarm.currentState() == 'online'):
                    if sensor == 'SENSOR_BREACH':
                        alarm.sensorBreach()
                    elif sensor == 'SENSOR_ESCALADE':
                        alarm.sensorBreach()
                    lcdControl.displayState(alarm.currentState(), alarm.currentStatus())

        if queue_nfc:
            with lock_nfc:
                cardUid = queue_nfc.popleft().decode("utf-8")
                print('CARD uid [%s]' % cardUid)
                if cardUid in validUid.values():
                    print ('REQ TOOGLE')
                    alarm.toggleState()
                else :
                    print ('NO VALID')
                lcdControl.displayState(alarm.currentState(), alarm.currentStatus())
                #print('DISPLAY state [%s]' % alarm.currentState())
                #print('DISPLAY status [%s]' % alarm.currentStatus())
                #continue
        sleep(.9)


# LCD
lcdControl = LcdControl()
lcdControl.display('Startup...')

# Controls
menuControl = MenuControl(running, queue_buttons, lock_buttons)

# Alarm status
alarm = Alarm()

# Alarm sensors
sensors = GpioSensor(running, queue_sensors, lock_sensors)

lcdControl.displayState(alarm.currentState(), alarm.currentStatus())

# NFC Thread
nfc = NfcReader(running, queue_nfc, lock_nfc)
nfc_thread = threading.Thread(target=nfc.nfc_reader)
nfc_thread.start()

#Run mainloop instead of threading it
#main_loop()

#Main thread
main_thread = threading.Thread(target=main_loop)
main_thread.start()

#Flask
app = Flask(__name__)

@app.route("/")
def home():
    return alarm.currentState() + alarm.currentStatus()

@app.route("/status/setOnline")
def setOnline():
    alarm.setOnline()
    lcdControl.displayState(alarm.currentState(), alarm.currentStatus())
    return 'ok'

@app.route("/status/setOffline")
def setOffline():
    alarm.setOffline()
    lcdControl.displayState(alarm.currentState(), alarm.currentStatus())
    return 'ok'

app.run()
