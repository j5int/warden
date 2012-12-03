import os
import sys
import threading

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

from twisted.scripts.twistd import ServerOptions
from twisted.application import app, service, internet
from twisted.python.runtime import platformType

# import platform specific twisted application runner
if platformType == "win32":
    from twisted.scripts._twistw import ServerOptions, WindowsApplicationRunner as _SomeApplicationRunner
else:
    from twisted.scripts._twistd_unix import ServerOptions, UnixApplicationRunner as _SomeApplicationRunner

from twisted.internet import reactor

class CarbonManager:
    """
    The main class for managing carbon daemons. A single reactor runs multiple
    twisted applications (the carbon daemons).

    Usage:
        manager = CarbonManager(carbon_dir)
        manager.add_daemon(CarbonManager.CACHE, optional_path_to_config_file)

        # < do work here >

        manager.stop_daemons()

    """

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
        if not os.path.exists(self.STORAGEDIR):
            os.makedirs(self.STORAGEDIR)

        self.active_thread = None


    def add_daemon(self, program, configfile=None):

        twistd_options = ["--no_save", "--nodaemon", program]

        if configfile != None:
            twistd_options.append('--config='+configfile)

        self.config = ServerOptions()
        self.config.parseOptions(twistd_options)

        self.appRunner = _SomeApplicationRunner(self.config)
        self.appRunner.preApplication()
        self.appRunner.application = self.appRunner.createOrGetApplication()
        service.IService(self.appRunner.application).services[0].startService()


    def start_daemons(self):
        self.active_thread = self.Carbonthread()
        self.active_thread.start()

    def stop_daemons(self, remove_pids=True):
        print('\nStopping reactor')
        self.active_thread.die()

        if remove_pids:

            pids = [os.path.join(self.STORAGEDIR, f) for f in os.listdir(self.STORAGEDIR) if f[-4:]=='.pid']

            for pidfile in pids:
                print('Removing old pidfile ' + pidfile)
                os.remove(pidfile)


    class Carbonthread(threading.Thread):

        def run(self):
            reactor.run(False)

        def die(self):
            reactor.stop()

