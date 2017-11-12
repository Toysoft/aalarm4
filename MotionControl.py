import subprocess
import os
import signal
from AlarmService import AlarmService

class MotionControl(AlarmService):
    def __init__(self, config):
        self.className = "Motion"

    def start(self):
        self.debug("Start motion service")
        proc = subprocess.Popen(['sudo', 'service', 'motion', 'start'])

    def stop(self):
        self.debug("Stop motion service")
        proc = subprocess.Popen(['sudo', 'service', 'motion', 'stop'])
