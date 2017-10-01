import subprocess
import os
import signal

class PlayControl(object):
    pid = None

    def __init__(self):
        print("Player init")

    def play(self):
        #self.pid = 1234
        # if not playerPid:
        #print(playerCommand)
        proc = subprocess.Popen(['/usr/bin/nohup','/usr/bin/mpg123','-@','/home/kemkem/playlist/list','-Z','&'])
        self.pid = proc.pid
        #print(playerPid)
        # else:
        #     print('player is already running')

    def stop(self):
        # if playerPid:
        print(self.pid)
        os.kill(self.pid, signal.SIGTERM)
        self.pid = None
        # else:
        #     print('player is not running')
