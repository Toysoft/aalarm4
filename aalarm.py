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
from MotionControl import MotionControl
from MailNotification import MailNotification
from Domoticz import Domoticz
from UiRestClient import UiRestClient

from AlarmService import AlarmService

from functools import wraps
from flask import request, Response

#REST calls
# import requests
# from requests.auth import HTTPBasicAuth

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

    #PlayControl
    playControl = None

    #MotionControl
    motionControl = None

    #Register keys control
    registerMode = None

    def __init__(self, config, running, queue, lock):
        self.className = "Alarm"
        self.running = running
        self.queue = queue
        self.lock = lock
        self.playControl = PlayControl(config)
        self.motionControl = MotionControl(config)
        self.registerMode = False

    def idleAction(self):
        self.debug("Run Idle actions")
        self.playControl.playIdle()

    def onlineAction(self):
        self.debug("Run Online actions")
        self.playControl.start()
        self.motionControl.start()

    def offlineAction(self):
        self.debug("Run Offline actions")
        self.playControl.stop()
        self.playControl.playOffline()
        self.motionControl.stop()

    def breachAction(self):
        self.debug("Run Breach actions")
        self.playControl.stop()
        self.playControl.playBreach()

    def warningAction(self):
        self.debug("Run Warning actions")
        self.playControl.playWarning()

    def alertAction(self):
        self.debug("Run Alert actions")
        self.playControl.playAlert()

    def toggleState(self, force=False):
        changed = False

        self.debug("Toggle state")
        #forced required online
        if force and self.status == 0:
            self.status = 2
            self.onlineAction()
            changed = True
        #idle
        elif self.status == 0:
            self.status = 1
            self.idleAction()
            changed = True
        #offline
        else:
            self.status = 0
            self.offlineAction()
            changed = True

        if(changed):
            self.stopTimers()
            with self.lock:
                self.queue.append('STATE')

    def toggleStateForce(self):
        self.toggleState(True)

    def toggleRegister(self):
        with self.lock:
            self.queue.append('REGISTER')

    def reportBreach(self, channel):
        #todo use channel
        self.escaladeState()

    def reportClose(self, channel):
        #idle to online
        if self.status == 1:
            self.status = 2;
            self.onlineAction()
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
        changed = False

        #breach
        if self.status == 2:
            changed = True
            self.status = 3;
            self.startTimers();
            self.breachAction()
        #warning
        elif self.status == 3:
            changed = True
            self.status = 4;
            self.warningAction()
        #alert
        elif self.status == 4:
            changed = True
            self.status = 5;
            self.alertAction()

        if(changed):
            self.debug('Escaladed to state ' + self.currentStatus())
            with self.lock:
                self.queue.append('ESCALADE')

    def currentStatus(self):
        return self.dStatusAlarm[self.status]

    def toggleRegisterMode(self):
        if self.registerMode:
            self.registerMode = False
        else:
            self.registerMode = True
        self.debug('registerMode ' + str(self.registerMode))

    def isRegisterMode(self):
        return self.registerMode

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
                        service.debug("<<<TODO>>>")
                        #nfc.keepNextUid()
                        #registerMode = True
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
                        uiRestClient.reportSensor('door', 'open')
                    #Sensor state changed to closed
                    elif patternClose.match(message):
                        sensor = matchClose.group(1)
                        alarm.reportClose(sensor)
                        uiRestClient.reportSensor('door', 'close')
                    lcdControl.displayState(alarm.currentStatus())

            if queue_alarm:
                with lock_alarm:
                    service.debug("Event : alarm")
                    message = queue_alarm.popleft()

                    if(message == "ESCALADE" or message == "STATE"):
                        if alarm.currentStatus() == 'alert':
                            mailer.sendMail('alert', 'alert has been triggered after a breach')
                        elif alarm.currentStatus() == 'online':
                            domoticz.call(config.configDomoticz('sceneLeave'))
                        elif alarm.currentStatus() == 'offline':
                            domoticz.call(config.configDomoticz('sceneEnter'))
                        else :
                            service.debug("Event : nothing to do")
                        lcdControl.displayState(alarm.currentStatus())
                        uiRestClient.reportState(alarm.currentStatus())
                    elif(message == "REGISTER"):
                        service.debug("Toggle registerMode")
                        alarm.toggleRegisterMode()

            if queue_nfc:
                with lock_nfc:
                    service.debug("Event : nfc")
                    cardUid = queue_nfc.popleft()#.decode("utf-8")
                    service.debug('Card uid [%s]' % cardUid)

                    if alarm.isRegisterMode():
                        service.debug("Registered")
                        uiRestClient.reportKeyRegistration(cardUid)
                        alarm.toggleRegisterMode()
                    else:
                        if cardUid in validUid.values():
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
    alarm = Alarm(config, running, queue_alarm, lock_alarm)

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

    #Rest client
    uiRestClient = UiRestClient(config)

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

    @app.route("/register")
    @requires_auth
    def modeRegister():
        alarm.toggleRegister()
        return 'ok'

    @app.route("/status/toggle")
    def toggle():
        alarm.toggleStateForce()
        lcdControl.displayState(alarm.currentStatus())
        return 'ok'

    app.run(host= '0.0.0.0')
