import os
import threading
from django.core import management
from warden_thread_mon import thread_async_raise

class GentryManager:

    def __init__(self):
        self.thread = self.GentryServerThread()

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.stop()

    def is_active(self):
        return True

    class GentryServerThread(threading.Thread):

        def run(self):
            print('Starting Gentry thread')

            os.environ['DJANGO_SETTINGS_MODULE'] = 'gentry.settings'

            management.execute_from_command_line(['manage.py', 'run'])

        def stop(self):
            thread_async_raise(self, KeyboardInterrupt)


