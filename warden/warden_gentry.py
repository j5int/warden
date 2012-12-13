import os
import sqlite3
import datetime
import threading
from django.core import management
from django.contrib.auth.hashers import PBKDF2PasswordHasher, get_random_string
from warden_thread_mon import thread_async_raise
from warden_logging import log

class GentryManager:

    def __init__(self, gentry_settings):
        self.settingsfile = gentry_settings

        os.environ['DJANGO_SETTINGS_MODULE'] = self.settingsfile

        from django.conf import settings
        self.database_path = settings.DATABASES['default']['NAME']
        # pull any settings in here if needed

        management.execute_from_command_line(['manage.py', 'syncdb','--noinput'])
        management.execute_from_command_line(['manage.py', 'migrate'])
        self.add_superuser('admin@admin.com', 'admin','admin')

        self.thread = self.GentryServerThread()


    def add_superuser(self, email, user, password):

        hasher = PBKDF2PasswordHasher()
        salt = get_random_string()
        phash = hasher.encode(user, salt)

        dtime = datetime.datetime.now()

        conn = None
        try:
            conn = sqlite3.connect(self.database_path)
            cur = conn.cursor()

            # first check for existing user with the same username
            cur.execute("SELECT * FROM auth_user WHERE username LIKE '%s'" % user)
            if(cur.rowcount == 0):
                cur.execute('INSERT INTO auth_user VALUES(?,?,?,?,?,?,?,?,?,?,?)',(0, user, user, user, email, phash, 1, 1, 1, dtime, dtime))
                conn.commit()
                log.debug('INSERTED new superuser, %s -> %s' % (user, phash))
            else:
                log.debug('A User with that username already exists')


        except Exception as e:
            raise e
        finally:
            if not conn:
                conn.close()

    def start(self):
        log.debug("Starting Gentry..")
        self.thread.start()
        log.debug("Started Gentry.")

    def stop(self):

        log.debug("Stopping Gentry..")
        self.thread.stop()
        self.thread.join()
        log.debug("Stopepd Gentry.")

    def is_active(self):
        if not self.thread.isAlive(): return False
        return True

    class GentryServerThread(threading.Thread):

        def __init__(self):
            threading.Thread.__init__(self)

        def run(self):
            management.execute_from_command_line(['manage.py', 'run'])

        def stop(self):
            thread_async_raise(self, KeyboardInterrupt)


