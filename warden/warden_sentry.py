import os
import imp
import sys
import time
import ctypes
import threading
import sentry.utils.runner as runner
from warden_utils import waitforsocket
from warden_thread_mon import thread_async_raise, get_thread_id
from logan.runner import sanitize_name, parse_args

from django.core import management
from optparse import OptionParser

import logan
import logan.settings

class SentryManager:
    """
    Doc stuff
    """

    def __init__(self, config_path=None, overwrite=False):
        """
        Defaults to default config path
        """


        os.environ['DJANGO_SETTINGS_MODULE'] = 'logan_config'

        # store old argument array
        self.old_argv = sys.argv
        self.config_path = config_path
        self.configuration = {}
        self.st = None

        if not os.path.exists(self.config_path) or overwrite:
            if os.path.exists(self.config_path):
                os.remove(self.config_path)

            try:
                logan.settings.create_default_settings(self.config_path, runner.generate_settings)

                cfg = open(self.config_path, 'a')
                cfg.write('SENTRY_WEB_SERVER=\'cherrypy\'')
                cfg.close()

            except OSError, e:
                raise e.__class__, 'Unable to write default settings file to %r' % self.config_path

        self.configuration = imp.new_module('temp_sentry_configuration')
        self.configuration.__file__ = self.config_path
        execfile(self.config_path, self.configuration.__dict__)

        print "Sentry Configuration file created at %r" % self.config_path


    def start_sentry(self):
        self.st = self.SentryThread(self.config_path)
        self.st.start()

    def stop_sentry(self):
        self.st.fire_keyboard_int()
        self.st.join()

    def is_active(self):
        webport = self.configuration.SENTRY_WEB_PORT
        return (waitforsocket('localhost',webport, 2, 1, 1))


    class SentryThread(threading.Thread):

        def __init__(self, config_file=None):
            threading.Thread.__init__(self)

            default_config_path='~/.sentry/sentry.conf.py'
            if 'SENTRY_CONF' in os.environ:
                default_config_path = os.environ.get('SENTRY_CONF')
            else:
                default_config_path = os.path.normpath(os.path.abspath(os.path.expanduser(default_config_path)))

            if config_file == None:
                self.config_file = os.path.expanduser(default_config_path)
            else:
                self.config_file = os.path.expanduser(config_file)

            if not os.path.exists(self.config_file):
                raise ValueError("Configuration file does not exist. Use 'sentry init' to initialize the file.")


        def run(self):

            os.environ['DJANGO_SETTINGS_MODULE'] = 'logan_config'

            def settings_callback(settings):
                runner.initialize_app({
                    'project': 'sentry',
                    'config_path': self.config_file,
                    'settings': settings,
                })

            logan.importer.install('logan_config', self.config_file, 'sentry.conf.server', allow_extras=True, callback=settings_callback)

            management.execute_from_command_line(['sentry', 'start'])


        def fire_keyboard_int(self):
            thread_async_raise(self, KeyboardInterrupt)


