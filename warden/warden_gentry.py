import os
import sqlite3
import datetime
import threading
from django.core import management
from django.contrib.auth.hashers import PBKDF2PasswordHasher, get_random_string
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
            imp.load_source('j5_warden_gentry_settings', warden_utils.normalize_path(self.settingsmodulepath))
            os.environ['DJANGO_SETTINGS_MODULE'] = 'j5_warden_gentry_settings'

        log.debug('$DJANGO_SETTINGS_MODULE = %s' % os.environ['DJANGO_SETTINGS_MODULE'])

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

        hasher = PBKDF2PasswordHasher()
        salt = get_random_string()
        phash = hasher.encode(password, salt)

        dtime = datetime.datetime.now()

        conn = None
        try:
            conn = sqlite3.connect(self.database_path)
            cur = conn.cursor()

            # first check for existing user with the same username
            cur.execute("SELECT * FROM auth_user WHERE username LIKE '%s'" % user)
            if cur.rowcount == 0:
                cur.execute('INSERT INTO auth_user VALUES(?,?,?,?,?,?,?,?,?,?,?)',(None, user, user, user, email, phash, 1, 1, 1, dtime, dtime))
                conn.commit()
                log.info('INSERTED new superuser, %s -> %s' % (user, phash))
            else:
                log.info('A User with that username already exists')


        except Exception as e:
            raise e
        finally:
            if not conn:
                conn.close()

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

            self.server = wsgiserver.CherryPyWSGIServer((self.host, self.port), application)

        def run(self):
            log.debug("Starting CherryPy server on %s:%s" % (self.host, self.port))
            self.server.start()

        def stop(self):
            log.debug("Shutting down CherryPy server...")
            self.server.stop()


