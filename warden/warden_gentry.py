import os
import threading
from django.core import management
from warden_logging import log
import logging
import sys
import warden_utils
import imp

class GentryManager:

    def __init__(self, gentry_settings_file=None):

        log.debug('Initialising Gentry..')

        if gentry_settings_file is None:
            os.environ['DJANGO_SETTINGS_MODULE'] = 'gentry.settings'
        else:
            n = 'j5_warden_gentry_settings'
            os.environ['DJANGO_SETTINGS_MODULE'] = n
            if not sys.modules.has_key(n):
                imp.load_source(n, warden_utils.normalize_path(gentry_settings_file))

        log.debug('$DJANGO_SETTINGS_MODULE = %s' % os.environ['DJANGO_SETTINGS_MODULE'])
        from django.conf import settings

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

        self.thread = self.GentryServerThread()


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

            from django.conf import settings

            from gentry.wsgi import application
            from cherrypy import wsgiserver

            self.host = settings.SENTRY_WEB_HOST
            self.port = settings.SENTRY_WEB_PORT

            self.key = settings.SENTRY_KEY

            self.server = wsgiserver.CherryPyWSGIServer((self.host, self.port), application)

        def run(self):
            log.debug("Starting CherryPy server on %s:%s with key '%s'" % (self.host, self.port, self.key))
            self.server.start()

        def stop(self):
            log.debug("Shutting down CherryPy server...")
            self.server.stop()


