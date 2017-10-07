import Adafruit_PN532 as PN532
from time import sleep
import binascii
from AlarmService import AlarmService

class NfcReader(AlarmService):
    pn532 = None

    CS   = 18
    MOSI = 23
    MISO = 24
    SCLK = 25

    running = None
    queue = None
    lock = None

    def __init__(self, running, queue, lock):
        self.className = "Nfc"
        self.running = running
        self.queue = queue
        self.lock = lock

        self.pn532 = PN532.PN532(cs=self.CS, sclk=self.SCLK, mosi=self.MOSI, miso=self.MISO)
        self.pn532.begin()
        ic, ver, rev, support = self.pn532.get_firmware_version()
        self.debug('Starting PN532 (firmware version: {0}.{1})'.format(ver, rev))
        self.pn532.SAM_configuration()

    def nfc_reader(self):
        while True:
            if not self.running:
                return

            uid = self.pn532.read_passive_target()

            if uid is None:
                continue

            cardUid = binascii.hexlify(uid)
            with self.lock:
                self.queue.append(cardUid)
            sleep(1)
