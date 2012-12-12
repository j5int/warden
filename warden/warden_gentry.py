import os
import sqlite3
import datetime
import threading
from django.core import management
from django.contrib.auth.hashers import PBKDF2PasswordHasher, get_random_string
from warden_thread_mon import thread_async_raise

class GentryManager:

    def __init__(self, gentry_settings):
        self.settingsfile = gentry_settings

        os.environ['DJANGO_SETTINGS_MODULE'] = self.settingsfile

        from django.conf import settings
        self.database_path = settings.DATABASES['default']['NAME']
        print(self.database_path)
        # pull any settings in here if needed

        self.thread = self.GentryServerThread()

    def initialise(self):
        management.execute_from_command_line(['manage.py', 'syncdb','--noinput'])
        management.execute_from_command_line(['manage.py', 'migrate'])
        self.add_superuser('admin@admin.com', 'admin','admin')

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
                print('INSERTED new superuser, %s -> %s' % (user, phash))
            else:
                print('A User with that username already exists')


        except Exception as e:
            print(e)
            print('failed to add new super user password, you may not be able to login. ')
        finally:
            if not conn:
                conn.close()





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


