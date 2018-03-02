import requests
from requests.auth import HTTPBasicAuth
from AlarmService import AlarmService

class Domoticz(AlarmService):
    login = None
    password = None
    enable = False

    def __init__(self, config):
        self.className = "Domoticz"
        self.login = config.configDomoticz('login')
        self.password = config.configDomoticz('password')
        if config.configDomoticz('enable') == 'yes':
            self.enable = True

    def call(self, url):
        self.debug('Call Domoticz url [%s]' % url)
        if self.enable:
            try:
                response = requests.get(url, auth=HTTPBasicAuth(self.login, self.password))
                #print(response)
            except:
                self.debug("Failed to call Domoticz")
