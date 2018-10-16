import logging
import sys

CLOCK_TIME = 1
THRESHOLD = 10000

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
        return self.logger
