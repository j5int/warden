import os
import sys
import configobj
import threading
from warden_logging import log
import logging
from warden_utils import normalize_path
import time
from diamond.server import Server

class DiamondManager:

    def __init__(self, diamond_root=None, diamond_conf_file=None, diamond_stdout_lvl=None):
        self.thread = None
        self.config = None

        log.debug('Initialising Diamond..')

        if diamond_root is not None:
            diamond_root = normalize_path(diamond_root)
            os.environ['DIAMOND_ROOT'] = diamond_root
            log.debug('$DIAMOND_ROOT=%s' % os.environ['DIAMOND_ROOT'])

        if diamond_conf_file is None:
            raise ValueError('DiamondManager: Path to diamond.conf was not supplied!')

        diamond_conf_file = normalize_path(diamond_conf_file)

        if os.path.exists(diamond_conf_file):
            self.config = configobj.ConfigObj(diamond_conf_file)
            self.config['configfile'] = diamond_conf_file
        else:
            print >> sys.stderr, "ERROR: Config file: %s does not exist." % diamond_conf_file
            sys.exit(1)

        if diamond_stdout_lvl is None:
            diamond_stdout_lvl = logging.ERROR

        self.log_diamond = logging.getLogger('diamond')
        self.log_diamond.setLevel(logging.DEBUG)
        self.log_diamond.propagate = False

        #       LOG to STDOUT
        formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(message)s]')
        streamHandler = logging.StreamHandler(sys.stdout)
        streamHandler.setFormatter(formatter)
        streamHandler.setLevel(diamond_stdout_lvl)

        # LOG to File
        fileHandler = logging.FileHandler(os.path.join(diamond_root,'diamond.log'))
        fileHandler.setFormatter(formatter)
        fileHandler.setLevel(logging.DEBUG)

        self.log_diamond.addHandler(streamHandler)
        self.log_diamond.addHandler(fileHandler)
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

        return self.thread.server.running

    class DiamondThread(threading.Thread):

        def __init__(self, config):
            threading.Thread.__init__(self)
            self.server = Server(config)

        def run(self):
            self.server.run()

        def stop(self):
            self.server.stop()
            self.server.scheduler.stop()



