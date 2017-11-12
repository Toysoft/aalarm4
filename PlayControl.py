import subprocess
import os
import signal
from AlarmService import AlarmService

class PlayControl(AlarmService):
    pid = None

    def __init__(self, config):
        self.className = "Player"

    def start(self):
        if self.pid:
            self.debug("A player instance is running, stopping it first")
            self.stop()
        self.debug("Start playing music")
        proc = subprocess.Popen(['/usr/bin/nohup','/usr/bin/mpg123','-@','/home/kemkem/playlist/list','-Z','&'])
        self.pid = proc.pid


    def stop(self):
        if self.pid:
            self.debug("Stop playing music")
            os.kill(self.pid, signal.SIGTERM)
            self.pid = None
        else:
            self.debug("No player running")
