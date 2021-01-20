import sys
from influxdb import InfluxDBClient

class InfluxCred():

    def __init__(self, args):

        self.host = args[0]
        self.port = args[1]
        self.username = args[2]
        self.password = args[3]
        self.deployment
:
