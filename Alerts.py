import requests
from requests.auth import HTTPBasicAuth

import smtplib

class Alerts(object):

    def __init__(self):
        print("Init alerts")

    def callDomoticz(subject, message):
        #print('call [%s]' % url)
        response = requests.get(url, auth=HTTPBasicAuth(configDomoticzLogin, configDomoticzPwd))
        print(response)

    def sendMail(subject, message):
        server = smtplib.SMTP(mailerStmpHost, mailerStmpPort)
        server.ehlo()
        server.starttls()
        server.login(mailerLogin, mailerPassword)

        subject = mailerSubjectPrefix + " " + subject

        BODY = '\r\n'.join(['To: %s' % mailerRecipient,
                            'From: %s' % mailerSender,
                            'Subject: %s' % subject,
                            '', message])

        try:
            server.sendmail(mailerSender, [mailerRecipient], BODY)
            print ('email sent')
        except:
            print ('error sending mail')

        server.quit()
