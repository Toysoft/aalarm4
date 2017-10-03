import requests
from requests.auth import HTTPBasicAuth

import smtplib

class Alerts(object):
    config = None

    def __init__(self, config):
        print("Init alerts")
        self.config = config

    def callDomoticz(self, subject, message):
        #print('call [%s]' % url)
        response = requests.get(url, auth=HTTPBasicAuth(configDomoticzLogin, configDomoticzPwd))
        print(response)

    def sendMail(self, subject, message):
        server = smtplib.SMTP(self.config.configMailer('stmpHost'), self.config.configMailer('stmpPort'))
        server.ehlo()
        server.starttls()
        server.login(self.config.configMailer('login'), self.config.configMailer('password'))

        subject = self.config.configMailer('subjectPrefix') + " " + subject

        BODY = '\r\n'.join(['To: %s' % self.config.configMailer('recipient'),
                            'From: %s' % self.config.configMailer('sender'),
                            'Subject: %s' % subject,
                            '', message])

        try:
            server.sendmail(self.config.configMailer('sender'), [self.config.configMailer('recipient')], BODY)
            print ('email sent')
        except:
            print ('error sending mail')

        server.quit()
