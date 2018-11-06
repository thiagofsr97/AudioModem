import logging
import sys

CLOCK_TIME = 1
BUFFERSIZE = 200
THRESHOLD = 6000
THRESHOLD_HIGH = 800
THRESHOLD_LOW = 500
PC_ADDRESS_1 = '000'
PC_ADDRESS_2 = '010'
PC_ADDRESS_3 = '100'
IP_ADDRESS_1 = '10.2'
IP_ADDRESS_2_1 = '10.15'
IP_ADDRESS_2_2 = '12.15'
IP_ADDRESS_3 = '12.4'


ROUTING_TABLE_1 = [['10.0', 4, PC_ADDRESS_2]]
ROUTING_TABLE_2 = [
    [IP_ADDRESS_1, 8, PC_ADDRESS_1],
    [IP_ADDRESS_3, 8, PC_ADDRESS_3]]
ROUTING_TABLE_3 = [['12.0', 4, PC_ADDRESS_2]]

EMPTY = -1
FRAME_FLAG = -2
K_SYMBOL = -3
N_ATTEMPTIVES = 10

class Logger:
    logger = None
    def get_instance(self, logger_name):
        if (self.logger and (logger_name != self.logger.name)) or not self.logger:
            self.logger = logging.getLogger(logger_name)
            self.logger.setLevel(logging.DEBUG)
            self.logger.handlers.clear()

            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

            ch = logging.FileHandler('Logging/' + logger_name + 'Logger.txt', mode='w')
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        return self.logger
