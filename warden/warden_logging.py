import sys
import logging
import settings

log = logging.getLogger('warden')

log.setLevel(settings.STDOUT_LEVEL)
log.propagate = False               #?

formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(message)s]')
streamHandler = logging.StreamHandler(sys.stdout)
streamHandler.setFormatter(formatter)
streamHandler.setLevel(settings.STDOUT_LEVEL)
log.addHandler(streamHandler)