import smtplib
from AlarmService import AlarmService

class MailNotification(AlarmService):
    smtpHost = None
    smtpPort = None
    login = None
    password = None
    subjectPrefix = None
    recipient = None
    sender = None

    def __init__(self, config):
        self.className = "Mailer"
        self.smtpHost = config.configMailer('stmpHost')
        self.smtpPort = config.configMailer('stmpPort')
        self.login = config.configMailer('login')
        self.password = config.configMailer('password')
        self.subjectPrefix = config.configMailer('subjectPrefix')
        self.recipient = config.configMailer('recipient')
        self.sender = config.configMailer('sender')

    def sendMail(self, subject, message):
        server = smtplib.SMTP(self.smtpHost, self.smtpPort)
        server.ehlo()
        server.starttls()
        server.login(self.login, self.password)

        subject = self.subjectPrefix + " " + subject

        BODY = '\r\n'.join(['To: %s' % self.recipient,
                            'From: %s' % self.sender,
                            'Subject: %s' % subject,
                            '', message])

        try:
            server.sendmail(self.recipient, [self.recipient], BODY)
            self.debug('Email sent')
        except:
            self.debug('Error sending mail')

        server.quit()
