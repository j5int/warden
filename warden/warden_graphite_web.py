import os
import sys
import time
import threading
import django.core.handlers.wsgi
from cherrypy import wsgiserver
from warden_utils import waitforsocket
from django.core import management
from warden_thread_mon import thread_async_raise, get_thread_id


class GraphiteWebManager():

    def __init__(self, webapp_dir, webapp_port):

        self.WEBAPP_DIR = webapp_dir
        self.WEBAPP_PORT = webapp_port

        self.graphite_thread = None
        self.graphite_application = None

        sys.path.append(self.WEBAPP_DIR)



    def start_graphite(self):

        os.environ['DJANGO_SETTINGS_MODULE'] = 'graphite.settings'

        from django.conf import settings


        import graphite.metrics.search



        self.graphite_application = django.core.handlers.wsgi.WSGIHandler()
        self.graphite_thread = self.GraphiteThread(self.WEBAPP_DIR, self.WEBAPP_PORT, self.graphite_application)
        self.graphite_thread.start()

    def stop_graphite(self):
        self.graphite_thread.stop()
        self.graphite_thread.join()

    def is_active(self):
        webport = self.WEBAPP_PORT
        return (waitforsocket('localhost',webport, 2, 1, 1))

    class GraphiteThread(threading.Thread):

        def __init__(self, webapp_path, webapp_port, application):
            threading.Thread.__init__(self)

            self.webapp_path = webapp_path
            self.port = webapp_port

            self.server = wsgiserver.CherryPyWSGIServer(('0.0.0.0',  self.port), application)


        def run(self):
            self.server.start()

        def stop(self):
            self.server.stop()

