import time
import unittest
import os
import tempfile

import random

from socket import socket
from ConfigParser import ConfigParser
import warden
from warden import CarbonManager

# Check dependencies
try:
    import whisper
except Exception as e:
    print('Missing required dependency: Whisper=0.9.10')
    exit(1)
try:
    import twisted
except Exception as e:
    print('Missing required dependency: Twisted=11.10.1')
    exit(1)

CARBON_SERVER = '127.0.0.1'
CARBON_PORT = 2003

class WardenCCTestCase(unittest.TestCase):

    step = 0
    max_datapoints = 0
    MAX_SAMPLE = 20

    @classmethod
    def setUpClass(cls):

        warden_dir = os.path.dirname(os.path.abspath(__file__))                       # this is the test dir
        carbon_dir = os.path.join(os.path.dirname(warden_dir), 'carbon')

        cls.temp_dir = tempfile.mkdtemp()
        os.environ["GRAPHITE_ROOT"] = cls.temp_dir

        test_conf = os.path.join(warden_dir, 'conf', 'carbon.conf')                # path to test config
        test_stor = os.path.join(warden_dir, 'conf', 'storage-schemas.conf')       # path to test config

        cls.manager = CarbonManager(carbon_dir)
        cls.manager.start_daemon(CarbonManager.CACHE, test_conf)

        # Extract test retentions from 'storage-schemas.conf'
        # Here we have assumed that 'storage-schemas.conf' only has one section;
        # this section must have a 'retention' option.
        config_parser = ConfigParser()
        if not config_parser.read(test_stor):
            print "Error: Couldn't read config file: %s" % test_stor

        retentions = ""

        secindex = config_parser.sections().index('carboncacheret')
        section = config_parser.sections()[secindex]
        options = dict(config_parser.items(config_parser.sections()[secindex]))
        retentions = whisper.parseRetentionDef(options['retentions'])

        cls.step = retentions[0]
        cls.max_datapoints = retentions[1]

        print(retentions)

        time.sleep(2)

    def runTest(self):

        tag = 'random_data'

        sock = socket()
        try:
            sock.connect( (CARBON_SERVER,CARBON_PORT) )
        except Exception as e:
            self.fail("could not connect")

        # Create some sample data
        num_data_points = min(self.MAX_SAMPLE, self.max_datapoints)
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

        print('data starts at: ' + str(data[0][0]))
        print('current time is:' + str(time.time()))
        print len(data)

        # check if data file was created

        tagFile = os.path.join(self.temp_dir, "storage","whisper","folder", tag + ".wsp")
        self.assertTrue(os.path.exists(tagFile))

        # check if data files contain correct data
        # print(whisper.info(tagFile))
        print 'from, until:', (now - self.step*(num_data_points), now)
        print(whisper.fetch(tagFile, now - self.step*(num_data_points), now))
        # The values passed to whisper.fetch for 'from' and 'to' are
        # rounded up to the next discrete time point. As a result, we subtract one step from them
        # Additionally, the upper limit is non-inclusive in the fetch
        # and so we need to increment our 'to' value by a step-size
        data_period_info, stored_data = whisper.fetch(tagFile, now - self.step*(num_data_points), now)
        # print len(stored_data)

        # Check that all fetched data corresponds to the data that was sent
        # (Note: some of the sent data may have rolled off the retained data
        # so only the fetched data that is still retained is compared)
        for whisper_data, sent_data in zip(reversed(stored_data), reversed(data)):
            self.assertAlmostEquals(whisper_data, sent_data[1])


    @classmethod
    def tearDownClass(cls):
        cls.manager.stop_daemons()
        print('done.')



def aggregate(data):
    return sum([d[1] for d in data])/len(data)

if __name__ == '__main__':
    unittest.main()

