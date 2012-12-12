import os
import threading
from django.core import management
from warden_thread_mon import thread_async_raise

class GentryManager:

    def __init__(self, gentry_settings):
        self.settingsfile = gentry_settings

        os.environ['DJANGO_SETTINGS_MODULE'] = self.settingsfile

        from django.conf import settings
        print('setts')
        print(vars(settings))
        # pull any settings in here if needed

        self.thread = self.GentryServerThread()

    def initialise(self):
        management.execute_from_command_line(['manage.py', 'syncdb','--noinput'])
        management.execute_from_command_line(['manage.py', 'migrate'])

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.stop()

    def is_active(self):
        if not self.thread.isAlive(): return False
        return True

    class GentryServerThread(threading.Thread):

        def __init__(self):
            threading.Thread.__init__(self)

        def run(self):
            print('Starting Gentry thread')

            management.execute_from_command_line(['manage.py', 'run'])

        def stop(self):
            thread_async_raise(self, KeyboardInterrupt)


