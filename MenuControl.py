import RPi.GPIO as GPIO
from AlarmService import AlarmService

class MenuControl(AlarmService):
    PIN_BT_SELECT = 26
    PIN_BT_UP = 19
    PIN_BT_DWN = 13
    dMenu = {0: 'Options', 1: 'Register NFC', 2: 'Exit'}
    dMenuQueue = {0: 'options', 1: 'register', 2: 'exit'}
    menuPos = 0

    def __init__(self, running, queue, lock):
        self.className = "Menu"
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
        self.debug("bt select")
        with self.lock:
            self.queue.append('MENU:' + self.dMenuQueue[self.menuPos])

    def callbackBtUp(self, channel):
        self.debug("bt up")
        self.menuPos = self.menuPos + 1
        if(self.menuPos > 2):
            self.menuPos = 0;
        with self.lock:
            self.queue.append('MENU:display')

    def callbackBtDown(self, channel):
        self.debug("bt down")
        self.menuPos = self.menuPos - 1
        if(self.menuPos < 0):
            self.menuPos = 2;
        with self.lock:
            self.queue.append('MENU:display')

    def currentMenu(self):
        self.debug("current " + self.dMenu[self.menuPos])
        return "Menu\n> " + self.dMenu[self.menuPos]
