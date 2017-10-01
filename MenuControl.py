import RPi.GPIO as GPIO

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
