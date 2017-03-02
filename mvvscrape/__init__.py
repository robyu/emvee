import logging
#
# logging
LOG_FILENAME='emvee.log'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    filemode='w')

logging.debug('logging initialized in mvvscrape/__init__')


