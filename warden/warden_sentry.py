import os
import sys
import time
import ctypes
import threading
import sentry.utils.runner as runner
from warden_thread_mon import thread_async_raise, get_thread_id

class SentryManager:
    """
    Doc stuff
    """

    def __init__(self, config_path):
        self.old_argv = []
        self.config_path = config_path
        self.st = None

    def start_sentry(self):
        # store old argument array
        self.old_argv = sys.argv

        # set new argument array
        sys.argv = ['sentry', '--config=%s' % self.config_path, 'start']

        # setup and start thread
        print('Starting Sentry with %s' % str(sys.argv))
        self.st = self.SentryThread()
        self.st.start()

    def stop_sentry(self):
        self.st.fire_keyboard_int()
        self.st.join()

    class SentryThread(threading.Thread):

        def __init__(self):
            threading.Thread.__init__(self)

        def run(self):
            runner.main()

        def fire_keyboard_int(self):
            thread_async_raise(self, KeyboardInterrupt)

def countdown(delay):
    while(delay>0):
        delay-=1
        time.sleep(1)
        print((delay * ' ') + str(delay))

if __name__=='__main__':
    sm = SentryManager('~/.sentry/sentry.conf.py')
    sm.start_sentry()

    countdown(100)

    sm.stop_sentry()

