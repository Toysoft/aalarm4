import subprocess
import os
import signal
from AlarmService import AlarmService

class PlayControl(AlarmService):
    pidMusic = None
    pidIdle = None
    pidOnline = None
    pidOffline = None
    pidBreach = None
    pidWarning = None
    pidAlert = None
    config = None

    def __init__(self, config):
        self.className = "Player"
        self.config = config

    def start(self, cmd):
        proc = subprocess.Popen(cmd)
        return proc.pid

    def kill(self, pid):
        if pid is not None:
            try:
                os.kill(pid, signal.SIGTERM)
            except:
                self.debug("No player running with this pid")

    def playMusic(self):
        if self.pidMusic:
            self.debug("A player instance is running, stopping it first")
            self.stop()
        # self.debug("Play Music")
        cmd = ['/usr/bin/nohup','/usr/bin/mpg123','-@','/home/kemkem/playlist/list','-Z','&']
        self.pidMusic = self.start(cmd)

    def stopMusic(self):
        self.kill(self.pidMusic)
        self.pidMusic = None

    def playIdle(self):
        cmd = ['/usr/bin/mpg123', self.config.configMedia("idle")]
        self.pidIdle = self.start(cmd)

    def playOnline(self):
        cmd = ['/usr/bin/mpg123', self.config.configMedia("online")]
        self.pidOnline = self.start(cmd)

    def playOffline(self):
        cmd = ['/usr/bin/mpg123', self.config.configMedia("offline")]
        self.pidOffline = self.start(cmd)

    def playBreach(self):
        cmd = ['/usr/bin/mpg123', self.config.configMedia("breach")]
        self.pidBreach = self.start(cmd)

    def playWarning(self):
        cmd = ['/usr/bin/mpg123', self.config.configMedia("warning")]
        self.pidWarning = self.start(cmd)

    def playAlert(self):
        cmd = ['/usr/bin/mpg123', self.config.configMedia("alert")]
        self.pidAlert = self.start(cmd)

    def stopAllNotifyPlayers(self):
        self.kill(self.pidIdle)
        self.kill(self.pidOnline)
        self.kill(self.pidOffline)
        self.kill(self.pidBreach)
        self.kill(self.pidWarning)
        self.kill(self.pidAlert)
        self.pidIdle = None
        self.pidOnline = None
        self.pidOffline = None
        self.pidBreach = None
        self.pidWarning = None
        self.pidAlert = None
