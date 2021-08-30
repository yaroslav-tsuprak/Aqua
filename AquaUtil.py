import math
import time


class AquaUtil(object):

    def checkHour(self, hour):
        return time.localtime().tm_hour == hour

    def checkTimeForFeeding(self, startH, stopH):
        current_hours = time.localtime().tm_hour
        return startH <= current_hours < stopH

    def checkTime(self, startH, stopH, startM):
        current_hours = time.localtime().tm_hour
        current_minutes = time.localtime().tm_min
        if startH <= current_hours < stopH:
            if current_minutes >= startM:
                return True
        return False

    def getSecondHours(self, startH, stopH):
        return math.floor(startH + ((stopH - startH) / 2) + 1)
