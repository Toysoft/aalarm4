class AlarmService(object):
    className = "None"

    def debug(self, message):
        print("[" + self.className +"] " + message)

    def setClassName(self, className):
        self.className = className
