import requests
from requests.auth import HTTPBasicAuth

class Domoticz(object):
    login = None
    password = None
    enable = False

    def __init__(self, config):
        self.login = config.configDomoticz('login')
        self.password = config.configDomoticz('password')
        if config.configDomoticz('enable') == 'yes':
            self.enable = True

    def call(self, url):
        print('call Domoticz url [%s]' % url)
        if self.enable:
            response = requests.get(url, auth=HTTPBasicAuth(self.login, self.password))
            print(response)
