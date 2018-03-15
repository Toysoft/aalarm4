import requests
from requests.auth import HTTPBasicAuth
from AlarmService import AlarmService

class UiRestClient(AlarmService):
    backendUrl = None
    backendLogin = None
    backendPassword = None

    def __init__(self, config):
        self.className = "UiRestClient"
        self.backendUrl = config.configUiBackend("url")
        self.backendLogin = config.configUiBackend("login")
        self.backendPassword = config.configUiBackend("password")

    def reportSensor(self, sensor, event):
        url = self.backendUrl + '/event/sensor?sensor=' + sensor + '&event=' + event
        try:
            response = requests.get(url, auth=HTTPBasicAuth(self.backendLogin, self.backendPassword))
        except:
            self.debug("Report sensor failed")

    def reportState(self, state):
        url = self.backendUrl + '/event/state?state=' + state
        try:
            response = requests.get(url, auth=HTTPBasicAuth(self.backendLogin, self.backendPassword))
        except:
            self.debug("Report state failed")

    def reportKeyRegistration(self, uid):
        url = self.backendUrl + '/keys/register?uid=' + uid
        try:
            response = requests.get(url, auth=HTTPBasicAuth(self.backendLogin, self.backendPassword))
        except:
            self.debug("Report key failed")

    def verifyKey(self, uid):
        url = self.backendUrl + '/keys/verify?uid=' + uid
        try:
            response = requests.get(url, auth=HTTPBasicAuth(self.backendLogin, self.backendPassword))
            self.debug(response.text)
            if response.text == 'accepted':
                return True
            else:
                return False
        except:
            self.debug("Verify key failed " + response)
