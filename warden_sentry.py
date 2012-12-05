import os
import sys
import time
import ctypes
import threading
from logan import importer
from logan.runner import run_app
from django.core import management
import sentry.utils.runner as runner
from ThreadRaise import thread_async_raise, get_thread_id
from sentry.services import http, udp

class SentryManager:

    def __init__(self):
        old_argv = sys.argv
        sys.argv = ['sentry','--config=~/.sentry/sentry.conf.py','start']
        print(sys.argv)
        self.st = None

    def start_sentry(self):
        self.st = self.SentryThread()
        self.st.start()

    def stop_sentry(self):
        self.st.fire_keyboard_int()

    class SentryThread(threading.Thread):

        def __init__(self):
            threading.Thread.__init__(self)



        def run(self):

            #svc = http.SentryHTTPServer(False, None, None, None)
            #svc.run()

            runner.main()


        def fire_keyboard_int(self):
            thread_async_raise(self, KeyboardInterrupt)

def countdown(delay):
    while(delay>0):
        delay-=1
        time.sleep(1)
        print((delay * ' ') + str(delay))

if __name__=='__main__':
    sm = SentryManager()
    sm.start_sentry()

    countdown(100)

    sm.stop_sentry()

