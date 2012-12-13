import os
import sys
import configobj
import threading
import logging

from diamond.server import Server

class DiamondManager:

    def __init__(self, configfile):
        self.thread = None
        self.config = None

        if os.path.exists(configfile):
            self.config = configobj.ConfigObj(os.path.abspath(configfile))
            self.config['configfile'] = configfile
        else:
            print >> sys.stderr, "ERROR: Config file: %s does not exist." % (configfile)
            sys.exit(1)

        self.log_diamond = logging.getLogger('diamond')
        self.log_diamond.setLevel(logging.DEBUG)
        self.log_diamond.propagate = False

#       LOG to STDOUT
        formatter = logging.Formatter('[%(asctime)s] [%(threadName)s] [%(message)s]')
        streamHandler = logging.StreamHandler(sys.stdout)
        streamHandler.setFormatter(formatter)
        streamHandler.setLevel(logging.DEBUG)
        self.log_diamond.addHandler(streamHandler)
        self.log_diamond.disabled = True

    def start(self):
        self.thread = self.DiamondThread(self.config)
        self.thread.start()

    def stop(self):
        self.thread.stop()

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

