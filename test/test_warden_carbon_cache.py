import time
import unittest
import os
import tempfile
import sys
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

from warden_carbon import CarbonManager                 # import from warden

temp_dir = tempfile.mkdtemp()
os.environ["GRAPHITE_ROOT"] = temp_dir

test_conf = os.path.join(test_dir, 'conf', 'carbon.conf')                # path to test config
test_stor = os.path.join(test_dir, 'conf', 'storage-schemas.conf')       # path to test config


class WardenCarbonCacheTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        self.manager = CarbonManager()
        self.manager.add_daemon(CarbonManager.CACHE, test_conf)
        self.manager.start_daemons()

        config_parser = ConfigParser()
        if not config_parser.read(test_stor):
            print "Error: Couldn't read config file: %s" % test_stor

        secindex = config_parser.sections().index('carboncache')
        section = config_parser.sections()[secindex]
        options = dict(config_parser.items(config_parser.sections()[secindex]))
        retentions = whisper.parseRetentionDef(options['retentions'])

        self.step = retentions[0]
        self.max_datapoints = retentions[1]
        self.max_sample = 20

        time.sleep(2)

        self.manager.print_status()

    def runTest(self):

        tag = 'random_data'

        sock = socket()
        try:
            sock.connect( (CARBON_SERVER,CARBON_PORT) )
        except Exception as e:
            self.fail("could not connect")

        # Create some sample data
        num_data_points = min(self.max_sample, self.max_datapoints)
        now = int(time.time())
        now -= now % self.step
        data = []
        lines = []
        for i in range(1, num_data_points+1):
            data.append((now - self.step*(num_data_points - i), random.random()*100))
            lines.append("folder.%s %s %d" % (tag, data[-1][1], data[-1][0]))

        message = '\n'.join(lines) + '\n' #all lines must end in a newline

        # debug
        print "sending message"
        print '-' * 70
        print message

        # send!
        sock.sendall(message)
        time.sleep(2) # NB - allows file operations to complete

        # check if data file was created

        tagFile = os.path.join(temp_dir, "storage","whisper","folder", tag + ".wsp")
        self.assertTrue(os.path.exists(tagFile))

        print(whisper.fetch(tagFile, now - self.step*(num_data_points), now))

        data_period_info, stored_data = whisper.fetch(tagFile, now - self.step*(num_data_points), now)

        for whisper_data, sent_data in zip(reversed(stored_data), reversed(data)):
            self.assertAlmostEquals(whisper_data, sent_data[1])


    @classmethod
    def tearDownClass(self):
        self.manager.stop_daemons()
        time.sleep(1)
        self.manager.print_status()
        print('done.')


if __name__ == '__main__':
    unittest.main()

