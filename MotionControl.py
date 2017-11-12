import subprocess
import os
import signal
from AlarmService import AlarmService

class MotionControl(AlarmService):
    def __init__(self, config):
        self.className = "Motion"

    def play(self):
        proc = subprocess.Popen(['service', 'motion', 'start'])

    def stop(self):
        proc = subprocess.Popen(['service', 'motion', 'stop'])
