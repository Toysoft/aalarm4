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

from AlarmService import AlarmService

from functools import wraps
from flask import request, Response

class Alarm(AlarmService):
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
        self.className = "Alarm"
        self.running = running
        self.queue = queue
        self.lock = lock

    def toggleState(self, force=False):
        self.debug("Toggle state")
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
        self.debug('Stop timers')

        if self.timerWarning is not None:
            self.debug('Stop warning')
            self.timerWarning.cancel()
        if self.timerAlert is not None:
            self.debug('Stop alert')
            self.timerAlert.cancel()

    def callbackEscalade(self, timerName):
        self.escaladeState()

        if timerName == 'warning':
            self.debug('Reached warning, warning expired')
            self.timerWarning = None
        if timerName == 'alert':
            self.debug('Reached alert, alert expired')
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
        self.debug('Escaladed to state ' + self.currentStatus())
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

    service = AlarmService()
    service.setClassName("Main")

    registerUidAuth = False
    registerUidAddNext = False

    def main_loop():
        lcdControl.displayState(alarm.currentStatus())
        while True:
            if queue_buttons:
                with lock_buttons:
                    button = queue_buttons.popleft()
                    if button == "MENU:exit":
                        service.debug("Exit from menu")
                        lcdControl.displayStateForced(alarm.currentStatus())
                    elif button == "MENU:register":
                        service.debug("Register a new NFC uid")
                        #nfc.keepNextUid()
                        registerUidAuth = True
                        registerUidAddNext = False
                    else:
                        lcdControl.display(menuControl.currentMenu())

            if queue_sensors:
                with lock_sensors:
                    service.debug("Event : sensor")
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
                    service.debug("Event : alarm")
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
                    service.debug("Event : nfc")
                    cardUid = queue_nfc.popleft()#.decode("utf-8")
                    service.debug('Card uid [%s]' % cardUid)
                    if cardUid in validUid.values():
                        if registerUidAuth :
                            lcdControl.display("Register master key ok")
                            registerUidAuth = False
                            registerUidAddNext = True
                        elif registerUidAddNext :
                            lcdControl.display("Added new uid")
                            registerUidAuth = False
                            registerUidAddNext = False
                            fileUidList = open("./uids",'w')
                            fileUidList.write(cardUid)
                            fileUidList.close()
                        else :
                            service.debug('Valid uid')
                            alarm.toggleState()
                    else :
                        service.debug('Unrecognized uid')
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

    def check_auth(username, password):
        return username == config.configServer("adminLogin") and password == config.configServer("adminPassword")

    def authenticate():
        return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

    def requires_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
            return f(*args, **kwargs)
        return decorated

    #Flask
    app = Flask(__name__)

    @app.route("/status")
    @requires_auth
    def status():
        return alarm.currentStatus()

    @app.route("/status/toggle")
    def toggle():
        alarm.toggleStateForce()
        lcdControl.displayState(alarm.currentStatus())
        return 'ok'

    app.run(host= '0.0.0.0')
