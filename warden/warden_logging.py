import sys
import logging

log = logging.getLogger('warden')

log.setLevel(logging.DEBUG)
log.propagate = False               #?

formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(message)s]')
streamHandler = logging.StreamHandler(sys.stdout)
streamHandler.setFormatter(formatter)
streamHandler.setLevel(logging.INFO)
log.addHandler(streamHandler)