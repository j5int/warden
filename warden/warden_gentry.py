import os
import threading
from django.core import management
from warden_logging import log
import logging
import sys
import warden_utils
import imp

class GentryManager:

    def __init__(self, settings):
        self.settingsmodulepath = settings.GENTRY_SETTINGS_PATH

        if self.settingsmodulepath is None:
            os.environ['DJANGO_SETTINGS_MODULE'] = 'gentry.settings'
        else:
            os.environ['DJANGO_SETTINGS_MODULE'] = 'j5_warden_gentry_settings'
            imp.load_source('j5_warden_gentry_settings', warden_utils.normalize_path(self.settingsmodulepath))

        n = os.environ['DJANGO_SETTINGS_MODULE']
        # import the string as a module
        s = __import__(n)
        # jump down the python path of the module to get the actual context for settings
        for p in n.split(".")[1:]:
            s = getattr(s, p)

        # set timezone here
        # ..

        # if there is a settings file value, that must be read and put into the settings module
        if hasattr(settings, 'SENTRY_KEY_FILE') and settings.SENTRY_KEY_FILE is not None:
            path = warden_utils.normalize_path(settings.SENTRY_KEY_FILE)
            log.debug("Overriding SENTRY_KEY from %s" % path)
            try:
                # read the key from the file
                f = open(path)
                key = f.readline().strip()
                f.close()

                if key == '':
                    log.error("Keyfile is empty, resorting to default")
                else:
                    s.SENTRY_KEY = key

            except IOError:
                log.error("Could not read overriding SENTRY_KEY_FILE")

        log.debug('$DJANGO_SETTINGS_MODULE = %s' % n)

        from django.conf import settings
        self.database_path = settings.DATABASES['default']['NAME']
        log.info('database_path is %s' % self.database_path)
        # pull any settings in here if needed

        # hook loggers
        import graphite.logger
        self.graphitelog = graphite.logger.log

        formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(message)s]')
        streamHandler = logging.StreamHandler(sys.stdout)
        streamHandler.setFormatter(formatter)
        streamHandler.setLevel(logging.DEBUG)

        self.graphitelog.infoLogger.addHandler(streamHandler)
        self.graphitelog.infoLogger.propagate = False

        self.graphitelog.exceptionLogger.addHandler(streamHandler)
        self.graphitelog.exceptionLogger.propagate = False

        self.graphitelog.cacheLogger.propagate = False
        if settings.LOG_CACHE_PERFORMANCE:
            self.graphitelog.cacheLogger.addHandler(streamHandler)

        self.graphitelog.renderingLogger.propagate = False
        if settings.LOG_RENDERING_PERFORMANCE:
            self.graphitelog.renderingLogger.addHandler(streamHandler)

        self.graphitelog.metricAccessLogger.propagate = False
        if settings.LOG_METRIC_ACCESS:
            self.graphitelog.metricAccessLogger.addHandler(streamHandler)


        management.execute_from_command_line(['manage.py', 'syncdb','--noinput'])
        management.execute_from_command_line(['manage.py', 'migrate'])
        self.add_superuser('admin@admin.com', 'admin','admin')


        self.thread = self.GentryServerThread()


    def add_superuser(self, email, user, password):

        from sentry.models import User, Model
        from django.db import IntegrityError
        try:
            u = User.objects.create_superuser(user, email, password)
            u.save()
            log.info('INSERTED new superuser, %s -> %s' % (user, password))
        except IntegrityError, e:
            log.info('A User with that username already exists')

    def start(self):
        self.thread.start()

    def stop(self):
        if self.thread.isAlive():
            self.thread.stop()
            self.thread.join()
        else:
            log.error("Can't stop Gentry if it has not started.")

    def is_active(self):

        if not self.thread.isAlive(): return False

        return self.thread.server.ready


    class GentryServerThread(threading.Thread):

        def __init__(self):
            threading.Thread.__init__(self)
            # name of the module to import "something.something.something.something"
            n = os.environ['DJANGO_SETTINGS_MODULE']

            # import the string as a module
            s = __import__(n)
            # jump down the python path of the module to get the actual context for settings
            for p in n.split(".")[1:]:
                s = getattr(s, p)

            from gentry.wsgi import application
            from cherrypy import wsgiserver

            self.host = s.SENTRY_WEB_HOST
            self.port = s.SENTRY_WEB_PORT

            self.key = s.SENTRY_KEY

            self.server = wsgiserver.CherryPyWSGIServer((self.host, self.port), application)

        def run(self):
            log.debug("Starting CherryPy server on %s:%s with key '%s'" % (self.host, self.port, self.key))
            self.server.start()

        def stop(self):
            log.debug("Shutting down CherryPy server...")
            self.server.stop()


