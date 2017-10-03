import requests
from requests.auth import HTTPBasicAuth

# import smtplib

class Domoticz(object):
    login = None
    password = None

    def __init__(self, config):
        print("Init config")
        self.login = config.configDomoticz('login')
        self.password = config.configDomoticz('password')

    def call(self, url):
        print('call Domoticz url [%s]' % url)
        response = requests.get(url, auth=HTTPBasicAuth(self.login, self.password))
        print(response)
