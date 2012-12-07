import os
import sys
import time
import socket
import shutil
import unittest
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))   # this is the test dir
warden_dir = os.path.dirname(test_dir)                  # warden root
sys.path.insert(0, warden_dir)

from warden_sentry import SentryManager

temp_dir = tempfile.mkdtemp()



class WardenSentryInitTestCase(unittest.TestCase):

    def test_sentry(self):
        print('Copying slim database into %s' % os.path.join(temp_dir, 'sentry.db'))
        shutil.copy2(os.path.join(test_dir, 'conf', 'sentry_slim.db'),os.path.join(temp_dir, 'sentry.db'))

        sm = SentryManager(os.path.join(temp_dir, 'sentry.conf.py'), overwrite=True)

        sm.start_sentry()   #start
        time.sleep(60)
        self.assertTrue(self.waitforsocket('localhost',9000))
        sm.stop_sentry()

if __name__=='__main__':
    unittest.main()
