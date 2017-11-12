import subprocess
import os
import signal
from AlarmService import AlarmService

class PlayControl(AlarmService):
    pid = None
    config = None

    def __init__(self, config):
        self.className = "Player"
        self.config = config

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

    def playIdle(self):
        subprocess.Popen(['/usr/bin/mpg123', self.config.configMedia("idle")])

    def playOnline(self):
        subprocess.Popen(['/usr/bin/mpg123', self.config.configMedia("online")])

    def playOffline(self):
            subprocess.Popen(['/usr/bin/mpg123', self.config.configMedia("offline")])

    def playBreach(self):
        subprocess.Popen(['/usr/bin/mpg123', self.config.configMedia("breach")])

    def playWarning(self):
        subprocess.Popen(['/usr/bin/mpg123', self.config.configMedia("warning")])

    def playAlert(self):
        subprocess.Popen(['/usr/bin/mpg123', self.config.configMedia("alert")])
