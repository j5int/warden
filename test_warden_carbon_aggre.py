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
CARBON_PORT = 2023

warden_dir = os.path.dirname(os.path.abspath(__file__))                       # this is the test dir
carbon_dir = os.path.join(os.path.dirname(warden_dir), 'carbon')

temp_dir = tempfile.mkdtemp()
os.environ["GRAPHITE_ROOT"] = temp_dir

test_conf = os.path.join(warden_dir, 'conf', 'carbon.conf')                # path to test config
test_stor = os.path.join(warden_dir, 'conf', 'storage-schemas.conf')       # path to test config

class WardenCarbonAggreTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.manager = CarbonManager(carbon_dir)
        self.manager.add_daemon(CarbonManager.CACHE, test_conf)
        self.manager.add_daemon(CarbonManager.AGGREGATOR, test_conf)
        self.manager.start_daemons()

        config_parser = ConfigParser()
        if not config_parser.read(test_stor):
            print "Error: Couldn't read config file: %s" % test_stor

        secindex = config_parser.sections().index('carbonaggre')
        section = config_parser.sections()[secindex]
        options = dict(config_parser.items(section))
        retentions = whisper.parseRetentionDef(options['retentions'])

        self.step = retentions[0]
        self.max_datapoints = retentions[1]
        self.max_sample = 20

        time.sleep(2)

    def runTest(self):

        tag = 'random_data_cca'

        sock = socket()
        try:
            sock.connect( (CARBON_SERVER,CARBON_PORT) )
        except Exception as e:
            self.fail("could not connect")

        # Create some sample data
        num_data_points = 4
        num_substep = 10

        data = []
        lines = []

        start = (time.time())
        start = start - (start % self.step)
        last = start


        stime = float(float(self.step)/float(num_substep))

        pts = (num_data_points)*(num_substep)
        tp = 0.0

        print('Bin is ' + str(self.step) + ' seconds.')
        print('Adding ' + str(1.0/stime) + ' points a second for ' + str(num_data_points*self.step) + ' seconds.')

        for i in range(num_data_points):

            to_aggregate = []

            for tick in range(num_substep):

                to_aggregate.append(  (last, random.random()*100)  )

                line = "folder.%s %s %d " % (tag, to_aggregate[-1][1], to_aggregate[-1][0])
                sock.sendall(line+'\n')
                print(line)

                tp+=1.0

                #print(str((tp/pts)*100) + '%')

                last += stime
                time.sleep(stime)


            aggregated_data = aggregate(to_aggregate)
            data.append(  aggregated_data  )
            print(aggregated_data)
            print('')

        print('')

        time.sleep(2) # NB - allows file operations to complete

        tagFile = os.path.join(temp_dir, "storage","whisper","folder", tag + ".wsp")

        self.assertTrue(os.path.exists(tagFile))
        data_period_info, stored_data = whisper.fetch(tagFile, start-1, time.time())
        print('Whisper data period : ' + str(data_period_info))
        print('Whisper data : ' + str(stored_data))
        print('Data expected: ' + str(data))
        print len(stored_data)
        print(zip(stored_data, data))
        for whisper_data, sent_data in zip(stored_data, data)[:-1]:     # :D
            self.assertAlmostEquals(whisper_data, sent_data)

    @classmethod
    def tearDownClass(self):
        self.manager.stop_daemons()
        print('done.')


def aggregate(data):
    return sum([d[1] for d in data])/len(data)

if __name__ == '__main__':
    unittest.main()

