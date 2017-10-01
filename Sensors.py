import RPi.GPIO as GPIO

class GpioSensor(object):
    PIN_SENSOR_1 = 6
    PIN_SENSOR_2 = 5

    running = None
    queue = None
    lock = None

    def __init__(self, running, queue, lock):
        self.running = running
        self.queue = queue
        self.lock = lock
        # GPIO.setup(self.PIN_SENSOR_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # GPIO.add_event_detect(self.PIN_SENSOR_1, GPIO.RISING, callback=self.callbackSensor, bouncetime=500)

        GPIO.setup(self.PIN_SENSOR_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.PIN_SENSOR_1, GPIO.BOTH, callback=self.callbackSensor, bouncetime=500)
        #GPIO.setup(self.PIN_SENSOR_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        #GPIO.add_event_detect(self.PIN_SENSOR_2, GPIO.FALLING, callback=self.callbackSensor, bouncetime=500)

    def callbackSensor(self,channel):
        print("GPIO sensor detect channel")
        if GPIO.input(channel):
            print("Rising (open to close)")
            with self.lock:
                self.queue.append('SENSOR_DOOR:{}:CLOSE'.format(channel))
        else:
            print("Falling (close to open)")
            with self.lock:
                self.queue.append('SENSOR_DOOR:{}:OPEN'.format(channel))


    # def callbackSensor(self,channel):
    #     #alarm.sensorBreach()
    #     #lcdControl.displayState(alarm.currentState(), alarm.currentStatus())
    #     print("GPIO sensor breach detect channel")
    #     print(channel)
    #     with self.lock:
    #         self.queue.append('SENSOR_BREACH')
