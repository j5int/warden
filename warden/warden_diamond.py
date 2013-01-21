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

    def __init__(self, settings):
        self.thread = None
        self.config = None

        configfile = normalize_path(settings.DIAMOND_CONFIG)

        if os.path.exists(configfile):
            self.config = configobj.ConfigObj(configfile)
            self.config['configfile'] = configfile
        else:
            print >> sys.stderr, "ERROR: Config file: %s does not exist." % configfile
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

    def ensure_path(self, section, var, path_tail):
        if not var in section:
            try:
                dr = os.environ['DIAMOND_ROOT']
                section[var] = os.path.join(dr, path_tail)
            except KeyError:
                print 'ERROR: Diamond missing path configuration [%s] AND $DIAMOND_ROOT has not been set!' % var
                exit(1)

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
            while True:
                time.sleep(1)


        def stop(self):
            time.sleep(2)
            self.server.stop()


