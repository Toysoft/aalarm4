import Adafruit_GPIO.MCP230xx as MCP
import Adafruit_CharLCD as LCD
from threading import Timer

class LcdControl(object):
    address = 0x20
    lines = 16
    cols = 2
    gpio = None
    lcd = None
    currentMenu = None
    timerBacklight = None
    TIMEOUT_BACKLIGHT = 10

    def __init__(self):
        self.gpio = MCP.MCP23008(self.address)
        self.lcd = LCD.Adafruit_CharLCD(1, 2, 3, 4, 5 , 6, self.lines, self.cols, gpio=self.gpio, backlight=7, invert_polarity=False)

    def display(self, message):
        print('LCD [%s]' % message)
        self.lcd.clear()
        self.lcd.message(message)
        self.lcd.backlightOn()
        if not self.timerBacklight:
            self.timerBacklight = Timer(self.TIMEOUT_BACKLIGHT,self.callBackBacklight)
            self.timerBacklight.start()

    def displayState(self, state, status):
        self.display('State [' + state + ']\n' + 'Status [' + status + ']')

    def displayMenu(self):
        self.display('Menu\nOptions')

    def menuButton(self, button):
        if not self.currentMenu:
            self.displayMenu()

    def callBackBacklight(self):
        self.lcd.backlightOff()
        self.timerBacklight = None