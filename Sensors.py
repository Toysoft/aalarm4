import RPi.GPIO as GPIO
from AlarmService import AlarmService

class GpioSensor(AlarmService):
    PIN_SENSOR_1 = 6
    PIN_SENSOR_2 = 5

    running = None
    queue = None
    lock = None

    def __init__(self, running, queue, lock):
        self.className = "Sensors"
        self.running = running
        self.queue = queue
        self.lock = lock
        GPIO.setup(self.PIN_SENSOR_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.PIN_SENSOR_1, GPIO.BOTH, callback=self.callbackSensor, bouncetime=200)

    def callbackSensor(self,channel):
        self.debug("GPIO sensor detect channel")
        if GPIO.input(channel):
            self.debug("Rising (open to close)")
            with self.lock:
                self.queue.append('SENSOR_DOOR:{}:CLOSE'.format(channel))
        else:
            self.debug("Falling (close to open)")
            with self.lock:
                self.queue.append('SENSOR_DOOR:{}:OPEN'.format(channel))
