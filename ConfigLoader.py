import configparser

class ConfigLoader(object):
    validUid = None
    mapConfig = None
    configParser = None

    def __init__(self):
        self.configParser = configparser.RawConfigParser()
        configFilePath = r'config'
        self.configParser.read(configFilePath)

        configNfckeys = self.configParser.get('nfc-keys', 'keys')

        self.validUid = {}
        self.mapConfig = {}

        for key_name in configNfckeys.split(','):
            print('Config NFC key [%s]' % key_name)
            key_value = self.configParser.get('nfc-keys', key_name)
            print('Config NFC value [%s]' % key_value)
            self.validUid[key_name] = key_value

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

    def addToMap(self, group, key):
        value = self.configParser.get(group, key)
        self.mapConfig[group + '/' + key] = value

    def configMailer(self, key):
        return self.mapConfig['mailer/' + key]

    def getValidUid(self):
        return self.validUid
