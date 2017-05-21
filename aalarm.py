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

import ConfigParser

class LcdControl(object):
    timeout = None
    gpio = None
    lcd = None
    currentMenu = None

    def __init__(self, address, lines, cols, backlight_pin, timeout):
        self.gpio = MCP.MCP23008(address)
        self.lcd = LCD.Adafruit_CharLCD(1, 2, 3, 4, 5 , 6, lines, cols, gpio=self.gpio, backlight=backlight_pin, invert_polarity=False)
        self.timeout = timeout

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
    state = 0
    dStateAlarm = {0: 'offline', 1: 'ready', 2: 'online'}
    dStatusAlarm = {0: 'nominal', 1: 'breach', 2: 'warning', 3: 'alert'}
    status = 0

    def toggleState(self):
        if self.state == 0:
            self.state = 1
        else:
            self.state = 0
            self.status = 0

    def setOnline(self):
        self.state = 2

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
        return self.dStateAlarm[self.state]

    def currentStatus(self):
        return self.dStatusAlarm[self.status]

    def isReady(self):
        if self.state == 1:
            return True
        return False

    def isWatching(self):
        if self.state == 2: #is online
            if self.status == 0: #is not aleady breach
                return True
        return False

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
    # PIN_SENSOR_2 = 5
    TIMEOUT_WARNING = 5
    TIMEOUT_ALERT = 10

    running = None
    queue = None
    lock = None

    def __init__(self, running, queue, lock):
        self.running = running
        self.queue = queue
        self.lock = lock
        GPIO.setup(self.PIN_SENSOR_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.PIN_SENSOR_1, GPIO.BOTH, callback=self.callbackSensor, bouncetime=500)
        # GPIO.setup(self.PIN_SENSOR_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # GPIO.add_event_detect(self.PIN_SENSOR_2, GPIO.FALLING, callback=self.callbackSensor, bouncetime=500)

    def callbackSensor(self,channel):
        event = "FALLING"
        if GPIO.input(channel):
            event = "RISING"
        with self.lock:
            self.queue.append('SENSOR_' + event)


#Threading queues and locks
queue_sensors = deque()
lock_sensors = threading.Lock()

queue_nfc = deque()
lock_nfc = threading.Lock()

queue_buttons = deque()
lock_buttons = threading.Lock()

running = True

#ConfigParser
configParser = ConfigParser.RawConfigParser()
configFilePath = r'config'
configParser.read(configFilePath)

#Load valid card keys
keys = configParser.get('nfc-keys', 'keys')
validUid = {}
for key_name in keys.split(','):
    key_value = configParser.get('nfc-keys', key_name)
    validUid[key_name] = key_value

#Timers
timerWarning = None
timerAlert = None

def setTimers(channel):
    timerWarning = Timer(5, callbackEscalade, args=[channel, 'warning'])
    timerAlert = Timer(10, callbackEscalade, args=[channel, 'alert'])
    timerWarning.start()
    timerAlert.start()

def callbackEscalade(channel, timerName):
    print('Escalade ' + timerName)
    if timerName == 'warning':
        timerWarning = None
    if timerName == 'alert':
        timerAlert = None
    alarm.sensorBreach()
    lcdControl.displayState(alarm.currentState(), alarm.currentStatus())

def stop():
    print('stop timers')
    if timerWarning is not None:
        print('stop warning')
        timerWarning.cancel()
    if timerAlert is not None:
        print('stop alert')
        timerAlert.cancel()

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

                if alarm.isReady():
                    if sensor == 'SENSOR_RISING':
                        alarm.setOnline()
                if alarm.isWatching():
                    if sensor == 'SENSOR_FALLING':
                        alarm.sensorBreach()
                        setTimers(6)

                lcdControl.displayState(alarm.currentState(), alarm.currentStatus())

        if queue_nfc:
            with lock_nfc:
                cardUid = queue_nfc.popleft()
                if cardUid in validUid.values():
                    alarm.toggleState()
                lcdControl.displayState(alarm.currentState(), alarm.currentStatus())
                #continue
        sleep(.9)


# LCD
#def __init__(self, address, lines, cols, backlight_pin, timeout):
lcdAddress = int(configParser.get('lcd', 'address'), 16)
lcdLines = int(configParser.get('lcd', 'lines'))
lcdCols = int(configParser.get('lcd', 'cols'))
lcdBacklightPin = int(configParser.get('lcd', 'backlight_pin'))
lcdTimeout = int(configParser.get('lcd', 'backlight_auto_off'))

lcdControl = LcdControl(address=lcdAddress, lines=lcdLines, cols=lcdCols, backlight_pin=lcdBacklightPin, timeout=lcdTimeout)
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
