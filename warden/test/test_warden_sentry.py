import os
import sys
import time
import socket
import unittest
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))   # this is the test dir
warden_dir = os.path.dirname(test_dir)                  # warden root
sys.path.insert(0, warden_dir)

from warden_sentry import SentryManager

temp_dir = tempfile.mkdtemp()



class WardenSentryTestCase(unittest.TestCase):

    def test_sentry(self):
        sm = SentryManager(os.path.join(temp_dir, 'sentry.conf.py'), overwrite=True)

        sm.start_sentry()   #start
        self.assertTrue(self.waitforsocket('localhost',9000))
        sm.stop_sentry()

        time.sleep(2)

        sm.start_sentry()
        self.assertTrue(self.waitforsocket('localhost',9000))
        sm.stop_sentry()

    def waitforsocket(self, host, port, timeout=300):
        start = time.time()
        while (time.time()-start)<timeout:
            try:
                s = socket.create_connection((host, port), timeout)
                s.close()
                print('Success')
                return True

            except Exception as e:
                print(e)

            time.sleep(8)
        print('Failed')
        return False

if __name__=='__main__':
    unittest.main()
