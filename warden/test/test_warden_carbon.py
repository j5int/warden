import time
import unittest
import os
import sys
import tempfile

import random

from socket import socket
from ConfigParser import ConfigParser

# Check dependencies
try:
    import whisper
except Exception as e:
    print('Missing required dependency: Whisper=0.9.10')
    exit(1)
try:
    import carbon
except Exception as e:
    print('Missing required dependency: Carbon=0.9.10')
    exit(1)
try:
    import twisted
except Exception as e:
    print('Missing required dependency: Twisted=11.10.1')
    exit(1)

CARBON_SERVER = '127.0.0.1'
CARBON_PORT = 2003

test_dir = os.path.dirname(os.path.abspath(__file__))   # this is the test dir
warden_dir = os.path.dirname(test_dir)                  # warden root
sys.path.insert(0, warden_dir)                          # add warden root to path

from warden_carbon import CarbonManager

temp_dir = tempfile.mkdtemp()

test_conf = os.path.join(test_dir, 'conf', 'carbon.conf')                # path to test config
test_stor = os.path.join(test_dir, 'conf', 'storage-schemas.conf')       # path to test config


class WardenCarbonTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.manager = None

    def runTest(self):

        self.manager = CarbonManager(test_conf, temp_dir)
        self.manager.add_daemon(CarbonManager.CACHE)
        self.manager.add_daemon(CarbonManager.AGGREGATOR)
        self.manager.start_daemons()

        time.sleep(1)
        self.manager.print_status()
        self.manager.stop_daemons()
        self.manager.print_status()
        self.manager = None

    @classmethod
    def tearDownClass(self):
        if self.manager != None:
            self.manager.stop_daemons()

if __name__ == '__main__':
    unittest.main()

