import subprocess
import os
import signal
from AlarmService import AlarmService

class PlayControl(AlarmService):
    pid = None

    def __init__(self, config):
        self.className = "Player"

    def start(self):
        #self.pid = 1234
        # if not playerPid:
        #print(playerCommand)
        self.debug("Start playing music")
        proc = subprocess.Popen(['/usr/bin/nohup','/usr/bin/mpg123','-@','/home/kemkem/playlist/list','-Z','&'])
        self.pid = proc.pid
        #print(playerPid)
        # else:
        #     print('player is already running')

    def stop(self):
        # if playerPid:
        self.debug("Stop playing music")
        #print(self.pid)
        os.kill(self.pid, signal.SIGTERM)
        self.pid = None
        # else:
        #     print('player is not running')
