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

        # FILE HANDLERS STDOUT
        self.graphitelog.metricAccessLogger.addHandler(self.make_and_return_filehandler('metricAccessLogger', os.path.expanduser('~/.graphite/metric_access.log')))
        self.graphitelog.cacheLogger.addHandler(self.make_and_return_filehandler('cacheLogger',  os.path.expanduser('~/.graphite/.graphite/cache.log')))
        self.graphitelog.renderingLogger.addHandler(self.make_and_return_filehandler('renderingLogger',  os.path.expanduser('~/.graphite/.graphite/rendering.log')))
        self.graphitelog.infoLogger.addHandler(self.make_and_return_filehandler('infoLogger',  os.path.expanduser('~/.graphite/.graphite/info.log')))
        self.graphitelog.exceptionLogger.addHandler(self.make_and_return_filehandler('exceptionLogger',  os.path.expanduser('~/.graphite/.graphite/exception.log')))

        # STREAM HANDLERS STDOUT
        self.graphitelog.metricAccessLogger.addHandler(self.make_and_return_streamhandler('metricAccessLogger'))
        self.graphitelog.cacheLogger.addHandler(self.make_and_return_streamhandler('cacheLogger'))
        self.graphitelog.renderingLogger.addHandler(self.make_and_return_streamhandler('renderingLogger'))
        self.graphitelog.infoLogger.addHandler(self.make_and_return_streamhandler('infoLogger'))
        self.graphitelog.exceptionLogger.addHandler(self.make_and_return_streamhandler('exceptionLogger'))

        self.graphitelog.infoLogger.propagate = False
        self.graphitelog.exceptionLogger.propagate = False
        self.graphitelog.cacheLogger.propagate = False
        self.graphitelog.metricAccessLogger.propagate = False
        self.graphitelog.renderingLogger.propagate = False

        dbfile = settings.DATABASES['default']['NAME']
        #exists
        try:
            with open(dbfile) as f: pass
            management.execute_from_command_line(['manage.py', 'migrate'])
        except:
            raise IOError('Gentry Database was not found at "%s". Please use warden-setup to initialise it.' % dbfile)

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


    def make_and_return_streamhandler(self, name):
        formatter = logging.Formatter('[%(asctime)s]['+name+'][%(message)s]')
        streamHandler = logging.StreamHandler(sys.stdout)
        streamHandler.setFormatter(formatter)
        streamHandler.setLevel(logging.DEBUG)
        return streamHandler

    def make_and_return_filehandler(self, name, file):
        formatter = logging.Formatter('[%(asctime)s]['+name+'][%(message)s]')
        streamHandler = logging.FileHandler(file)
        streamHandler.setFormatter(formatter)
        streamHandler.setLevel(logging.DEBUG)
        return streamHandler


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


