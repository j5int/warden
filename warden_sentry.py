import sys
import time
import ctypes
import threading
from logan.runner import run_app
import sentry.utils.runner as runner
from ThreadRaise import thread_async_raise, get_thread_id


class SentryManager:

    def __init__(self):
        old_argv = sys.argv
        sys.argv = ['sentry','start']
        self.st = None

    def start_sentry(self):
        self.st = self.SentryThread()
        self.st.start()

    def stop_sentry(self):
        self.st.die()

    class SentryThread(threading.Thread):
        def run(self):
            #import pdb; pdb.set_trace()
            run_app(
                project='sentry',
                default_config_path='~/.sentry/sentry.conf.py',
                default_settings='sentry.conf.server',
                settings_initializer=runner.generate_settings,
                settings_envvar='SENTRY_CONF',
                initializer=runner.initialize_app,
            )

        def die(self):
            thread_async_raise(self, KeyboardInterrupt)

def countdown(delay):
    while(delay>0):
        delay-=1
        time.sleep(1)
        print((delay * ' ') + str(delay))

if __name__=='__main__':
    sm = SentryManager()
    sm.start_sentry()

    countdown(10)

    sm.stop_sentry()

