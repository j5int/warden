import os
import sys
import configobj
import threading
from warden_logging import log
import logging

from diamond.server import Server

class DiamondManager:

    def __init__(self, settings):
        self.thread = None
        self.config = None

        configfile = os.path.expanduser(settings.DIAMOND_CONFIG)

        if os.path.exists(configfile):
            self.config = configobj.ConfigObj(os.path.abspath(configfile))
            self.config['configfile'] = configfile
        else:
            print >> sys.stderr, "ERROR: Config file: %s does not exist." % (configfile)
            sys.exit(1)

        self.log_diamond = logging.getLogger('diamond')
        self.log_diamond.setLevel(settings.DIAMOND_STDOUT_LEVEL)
        self.log_diamond.propagate = False

#       LOG to STDOUT
        formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(message)s]')
        streamHandler = logging.StreamHandler(sys.stdout)
        streamHandler.setFormatter(formatter)
        streamHandler.setLevel(settings.DIAMOND_STDOUT_LEVEL)
        self.log_diamond.addHandler(streamHandler)
        self.log_diamond.disabled = False
        
    def start(self):
        log.debug("Starting Diamond..")
        self.thread = self.DiamondThread(self.config)
        self.thread.start()

        log.debug("Started Diamond.")

    def stop(self):
        if self.thread.isAlive():
            log.debug("Stopping Diamond..")
            self.thread.stop()
            self.thread.join()
            log.debug("Stopped Diamond.")
        else:
            log.error("Can't stop Diamond if it has not started.")

    def is_active(self):
        if not self.thread:
            return False

        return self.thread.isAlive()

    class DiamondThread(threading.Thread):

        def __init__(self, config):
            threading.Thread.__init__(self)
            self.server = Server(config)

        def run(self):
            self.server.run()

        def stop(self):
            self.server.stop()

