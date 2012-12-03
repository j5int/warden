import os
import sys
import time
import psutil
import string
import threading
from optparse import OptionParser

# Check major dependencies
try:
    import whisper
except Exception as e:
    print('Missing required dependency: Whisper=0.9.10')
    exit(1)
try:
    import carbon
except Exception as e:
    print('Missing required dependency: Carbon=0.9.10')
    exit(1)
try:
    import twisted
except Exception as e:
    print('Missing required dependency: Twisted=11.10.1')
    exit(1)

from twisted.scripts.twistd import ServerOptions, runApp
from twisted.application import app, service, internet
from twisted.python.runtime import platformType

# import platform specific twisted application runner
if platformType == "win32":
    from twisted.scripts._twistw import ServerOptions, WindowsApplicationRunner as _SomeApplicationRunner
else:
    from twisted.scripts._twistd_unix import ServerOptions, UnixApplicationRunner as _SomeApplicationRunner

# import and create reactor, this is also platform specific
from twisted.internet import reactor

class CarbonManager:

    CACHE = 'carbon-cache'
    AGGREGATOR = 'carbon-aggregator'
    RELAY = 'carbon-relay'

    def __init__(self, path_to_carbon):
        self.PATHTOCARBON = path_to_carbon
        self.BINDIR = os.path.join(self.PATHTOCARBON, 'bin')
        self.LIBDIR = os.path.join(self.PATHTOCARBON, 'lib')
        sys.path.insert(0, self.LIBDIR)

        self.GRAPHITEROOT = os.environ['GRAPHITE_ROOT']
        self.STORAGEDIR = os.path.join(self.GRAPHITEROOT, 'storage')
        os.makedirs(self.STORAGEDIR)

        self.active_threads = []

    def start_daemon(self, program, configfile=None):
        t = self.Carbonthread(program, os.path.join(self.BINDIR, program+'.py'), configfile)
        t.start()
        self.active_threads.append(t)

    def stop_daemons(self):
        print('\nStopping reactor')
        reactor.crash()
        reactor.getThreadPool().stop()
        reactor.disconnectAll()

        nthread = len(self.active_threads)
        for t in self.active_threads:
            t.join()

        print('Stopped %d daemons' % nthread)


    class Carbonthread(threading.Thread):

        def __init__(self, program, filename, configfile=None):
            threading.Thread.__init__(self)

            twistd_options = ["--no_save", "--nodaemon", program]

            if configfile != None:
                twistd_options.append('--config='+configfile)

            """
            # Additional argument parsing, not sure if needed. I have a feeling twisted does not need a full file path
            # if carbon is installed properly on the system. 'start' is also not needed when run in this threaded way.
            from carbon.conf import get_parser
            parser = get_parser(program)
            # options are the specific wanted things, args are the leftovers that may be needed for twisted
            (options, args) = parser.parse_args([filename, 'start'])
            twistd_options.extend(args) # add leftovers
            """

            self.config = ServerOptions()
            self.config.parseOptions(twistd_options)

        def run(self):
            self.appRunner = _SomeApplicationRunner(self.config)
            self.appRunner.preApplication()
            self.appRunner.application = self.appRunner.createOrGetApplication()

            if platformType == "win32":
                service.IService(self.appRunner.application).privilegedStartService()
                app.startApplication(self.appRunner.application, not self.appRunner.config['no_save'])
                app.startApplication(internet.TimerService(0.1, lambda:None), 0)
            else:
                self.appRunner.startApplication(self.appRunner.application)

            try:
                reactor.run(False)
            except Exception as e:
                print('Reactor has already started.')


