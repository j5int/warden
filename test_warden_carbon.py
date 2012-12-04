import time
import unittest
import os
import tempfile

import random

from socket import socket
from ConfigParser import ConfigParser
from warden_carbon import CarbonManager

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

warden_dir = os.path.dirname(os.path.abspath(__file__))                       # this is the test dir
carbon_dir = os.path.join(os.path.dirname(warden_dir), 'carbon')

temp_dir = tempfile.mkdtemp()
os.environ["GRAPHITE_ROOT"] = temp_dir

test_conf = os.path.join(warden_dir, 'conf', 'carbon.conf')                # path to test config
test_stor = os.path.join(warden_dir, 'conf', 'storage-schemas.conf')       # path to test config


class WardenCarbonTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.manager = None

    def runTest(self):

        self.manager = CarbonManager(carbon_dir)
        self.manager.add_daemon(CarbonManager.CACHE, test_conf)
        self.manager.add_daemon(CarbonManager.AGGREGATOR, test_conf)
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

