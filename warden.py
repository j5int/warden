import os
import sys
import time
import psutil
import string
import threading

from optparse import OptionParser


PATHTOCARBON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'carbon')
GRAPHITEROOT = os.environ['GRAPHITE_ROOT']
BINDIR = os.path.join(PATHTOCARBON, 'bin')
STORAGEDIR = os.path.join(GRAPHITEROOT, 'storage')

LIBDIR = os.path.join(PATHTOCARBON, 'lib')
sys.path.insert(0, LIBDIR)


from carbon.conf import get_parser
from twisted.scripts.twistd import ServerOptions, runApp
from twisted.application import app, service, internet

from twisted.python.runtime import platformType

if platformType == "win32":
    from twisted.scripts._twistw import ServerOptions, \
        WindowsApplicationRunner as _SomeApplicationRunner
else:
    from twisted.scripts._twistd_unix import ServerOptions, \
        UnixApplicationRunner as _SomeApplicationRunner


from twisted.internet import reactor

class Carbonthread(threading.Thread):

    #thread types
    CACHE = 'carbon-cache'
    AGGREGATOR = 'carbon-aggregator'
    RELAY = 'carbon-relay'

    def __init__(self, program):
        self.program = program
        threading.Thread.__init__(self)
        parser = get_parser(self.program)
        # options are the specific wanted things, args are the leftovers that may be needed for twisted
        (options, args) = parser.parse_args([os.path.join(BINDIR, self.program+'.py'), 'start'])

        twistd_options = ["--no_save", "--nodaemon", self.program]
        twistd_options.extend(args) # add left overs

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


    def stop(self):
        print('Stopping reactor')
        reactor.crash()
        reactor.getThreadPool().stop()
        reactor.disconnectAll()

