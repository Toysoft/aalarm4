from time import sleep
import threading
from collections import deque
from threading import Timer
from flask import Flask
import time
import re

from LcdControl import LcdControl
from MenuControl import MenuControl
from Sensors import GpioSensor
from Nfc import NfcReader
from ConfigLoader import ConfigLoader
from PlayControl import PlayControl
from MailNotification import MailNotification
from Domoticz import Domoticz

class Alarm(object):
    dStatusAlarm = {0: 'offline', 1: 'idle', 2: 'online', 3: 'breach', 4: 'warning', 5: 'alert'}
    status = 0

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

    def toggleState(self, force=False):
        print("Toggle state")
        if force and self.status == 0:
            self.status = 2
        elif self.status == 0:
            self.status = 1
        else:
            self.status = 0
        self.stopTimers()
        with self.lock:
            self.queue.append('STATE')

    def toggleStateForce(self):
        self.toggleState(True)

    def reportBreach(self, channel):
        #todo use channel
        self.escaladeState()

    def reportClose(self, channel):
        if self.status == 1:
            self.status = 2;
        with self.lock:
            self.queue.append('ESCALADE')

    def startTimers(self):
        if not self.timerWarning:
            self.timerWarning = Timer(self.TIMEOUT_WARNING,self.callbackEscalade,args=['warning'])
            self.timerWarning.start()
            self.timerAlert = Timer(self.TIMEOUT_ALERT,self.callbackEscalade,args=['alert'])
            self.timerAlert.start()

    def stopTimers(self):
        print('stop timers')

        if self.timerWarning is not None:
            print(' stop warning')
            self.timerWarning.cancel()
        if self.timerAlert is not None:
            print(' stop alert')
            self.timerAlert.cancel()

    def callbackEscalade(self, timerName):
        self.escaladeState()

        if timerName == 'warning':
            print('reached warning, warning expired')
            self.timerWarning = None
        if timerName == 'alert':
            print('reached alert, alert expired')
            self.timerAlert = None

    def escaladeState(self):
        #breach
        if self.status == 2:
            self.status = 3;
            self.startTimers();
        #warning
        elif self.status == 3:
            self.status = 4;
        #alert
        elif self.status == 4:
            self.status = 5;
        print('Escaladed to state ' + self.currentStatus())
        with self.lock:
            self.queue.append('ESCALADE')

    def currentStatus(self):
        return self.dStatusAlarm[self.status]

if __name__ == '__main__':
    #Threading queues and locks
    queue_alarm = deque()
    lock_alarm = threading.Lock()

    queue_sensors = deque()
    lock_sensors = threading.Lock()

    queue_nfc = deque()
    lock_nfc = threading.Lock()

    queue_buttons = deque()
    lock_buttons = threading.Lock()

    running = True

    #ConfigParser
    config = ConfigLoader()
    validUid = config.getValidUid()

    def main_loop():
        lcdControl.displayState(alarm.currentStatus())
        while True:
            if queue_buttons:
                with lock_buttons:
                    button = queue_buttons.popleft()
                    print('button ' + button)
                    lcdControl.menuButton(button)

            if queue_sensors:
                with lock_sensors:
                    message = queue_sensors.popleft()

                    patternOpen = re.compile('SENSOR_DOOR:(\d+):OPEN')
                    patternClose = re.compile('SENSOR_DOOR:(\d+):CLOSE')

                    matchOpen = patternOpen.match(message);
                    matchClose = patternClose.match(message);

                    #Breach is reported by a sensor
                    if patternOpen.match(message):
                        sensor = matchOpen.group(1)
                        alarm.reportBreach(sensor)
                    #Sensor state changed to closed
                    elif patternClose.match(message):
                        sensor = matchClose.group(1)
                        alarm.reportClose(sensor)
                    lcdControl.displayState(alarm.currentStatus())

            if queue_alarm:
                with lock_alarm:
                    message = queue_alarm.popleft()

                    if alarm.currentStatus() == 'alert':
                        mailer.sendMail('alert', 'alert has been triggered after a breach')
                    if alarm.currentStatus() == 'online':
                        domoticz.call(config.configDomoticz('sceneLeave'))
                    if alarm.currentStatus() == 'offline':
                        domoticz.call(config.configDomoticz('sceneEnter'))

                    lcdControl.displayState(alarm.currentStatus())

            if queue_nfc:
                with lock_nfc:
                    cardUid = queue_nfc.popleft().decode("utf-8")
                    print('CARD uid [%s]' % cardUid)
                    if cardUid in validUid.values():
                        alarm.toggleState()
                    else :
                        print ('NO VALID')
                    lcdControl.displayState(alarm.currentStatus())
            sleep(.9)

    # LCD
    lcdControl = LcdControl()
    lcdControl.display('Startup...')

    # Controls
    menuControl = MenuControl(running, queue_buttons, lock_buttons)

    # Alarm status
    alarm = Alarm(running, queue_alarm, lock_alarm)

    # Alarm sensors
    sensors = GpioSensor(running, queue_sensors, lock_sensors)

    #lcdControl.displayState(alarm.currentStatus())

    # NFC Thread
    nfc = NfcReader(running, queue_nfc, lock_nfc)
    nfc_thread = threading.Thread(target=nfc.nfc_reader)
    nfc_thread.start()

    #Mailing system
    mailer = MailNotification(config)

    #Domoticz rest controls
    domoticz = Domoticz(config)

    #Main thread
    main_thread = threading.Thread(target=main_loop)
    main_thread.start()

    #Flask
    app = Flask(__name__)

    @app.route("/status")
    def status():
        return alarm.currentStatus()

    @app.route("/status/toggle")
    def toggle():
        alarm.toggleStateForce()
        lcdControl.displayState(alarm.currentStatus())
        return 'ok'

    app.run()
