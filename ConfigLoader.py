import configparser
from AlarmService import AlarmService

class ConfigLoader(AlarmService):
    validUid = None
    mapConfig = None
    configParser = None

    def __init__(self):
        self.className = "Config"
        self.configParser = configparser.RawConfigParser()
        configFilePath = r'config'
        self.configParser.read(configFilePath)

        configNfckeys = self.configParser.get('nfc-keys', 'keys')

        self.validUid = {}
        self.mapConfig = {}

        for key_name in configNfckeys.split(','):
            self.debug('Config NFC key [%s]' % key_name)
            key_value = self.configParser.get('nfc-keys', key_name)
            self.debug('Config NFC value [%s]' % key_value)
            self.validUid[key_name] = key_value

        self.addToMap('domoticz', 'enable')
        self.addToMap('domoticz', 'login')
        self.addToMap('domoticz', 'password')

        self.addToMap('domoticz', 'sceneLeave')
        self.addToMap('domoticz', 'sceneEnter')

        self.addToMap('mailer', 'recipient')
        self.addToMap('mailer', 'sender')
        self.addToMap('mailer', 'subjectPrefix')
        self.addToMap('mailer', 'stmpHost')
        self.addToMap('mailer', 'stmpPort')
        self.addToMap('mailer', 'login')
        self.addToMap('mailer', 'password')

        self.addToMap('player', 'command')

        self.addToMap('server', 'adminLogin')
        self.addToMap('server', 'adminPassword')

        self.addToMap('uibackend', 'url')
        self.addToMap('uibackend', 'login')
        self.addToMap('uibackend', 'password')

        self.addToMap('media', 'idle')
        self.addToMap('media', 'warning')
        self.addToMap('media', 'alert')

    def addToMap(self, group, key):
        value = self.configParser.get(group, key)
        self.mapConfig[group + '/' + key] = value

    def configMailer(self, key):
        return self.mapConfig['mailer/' + key]

    def configDomoticz(self, key):
        return self.mapConfig['domoticz/' + key]

    def configServer(self, key):
        return self.mapConfig['server/' + key]

    def configUiBackend(self, key):
        return self.mapConfig['uibackend/' + key]

    def configMedia(self, key):
        return self.mapConfig['media/' + key]

    def getValidUid(self):
        return self.validUid
