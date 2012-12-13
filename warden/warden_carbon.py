import os
import threading
from warden_utils import waitforsocket
from warden_logging import log
from ConfigParser import SafeConfigParser

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

# import the global reactor object, this is initialised HERE! and cannot be instanced
from twisted.internet import reactor

class CarbonManager:
    """
    The main class for managing carbon daemons. A single reactor runs multiple
    twisted applications (the carbon daemons). This is quite like Twistd

    Usage:
        manager = CarbonManager(carbon_directory)
        manager.add_daemon(CarbonManager.CACHE, optional_path_to_config_file)
        manager.start_daemons()

        manager.stop_daemons()

        manager.print_status() # to print the current status of the reactor and app runners
    """

    CACHE = 'carbon-cache'
    AGGREGATOR = 'carbon-aggregator'
    RELAY = 'carbon-relay'

    def __init__(self, carbon_config_file, daemons=[], new_graphite_root=None):
        """
        Build the storage directory and prepare for Start. The storage directory
        is in the GRAPHITE_ROOT folder which is used by all of the carbon daemons.
        GRAPHITE_ROOT can be modified as shown by:
            os.environ["GRAPHITE_ROOT"] = some_storage_directory
        """

        log.debug("Initialising Carbon")
        if new_graphite_root != None:
            os.environ["GRAPHITE_ROOT"] = new_graphite_root

        self.GRAPHITE_ROOT = os.environ['GRAPHITE_ROOT']

        log.debug("$GRAPHITE_ROOT = %s" % self.GRAPHITE_ROOT)

        self.STORAGEDIR = os.path.join(self.GRAPHITE_ROOT, 'storage')
        if not os.path.exists(self.STORAGEDIR):
            os.makedirs(self.STORAGEDIR)

        self.reactor_thread = None

        self.application_runners = []

        self.carbon_config_file = carbon_config_file

        self.configuration = SafeConfigParser()
        self.configuration.read(self.carbon_config_file)

        self.daemons = daemons

        log.debug("Carbon Daemons = %s" % self.daemons)


    def add_daemon(self, program):
        if reactor.running:                                                     # this is just for sanity, it may be unnecessary
            raise Exception('Cannot add daemon. Reactor is already running.')

        twistd_options = ["--no_save", "--nodaemon", program]

        if self.carbon_config_file != None:
            twistd_options.append('--config='+self.carbon_config_file)

        self.config = ServerOptions()
        self.config.parseOptions(twistd_options)
        self.config['originalname'] = program

        appRunner = _SomeApplicationRunner(self.config)
        appRunner.preApplication()
        appRunner.application = appRunner.createOrGetApplication()
        service.IService(appRunner.application).services[0].startService()
        self.application_runners.append(appRunner)

    def start_daemons(self):
        log.debug("Starting Carbon..")

        for d in self.daemons:
            self.add_daemon(d)

        if reactor.running:
            raise Exception('Reactor is already running.')
        self.reactor_thread = self.ReactorThread()
        self.reactor_thread.start()

        log.debug("Started Carbon.")

    def stop_daemons(self, remove_pids=True):
        log.debug("Stopping Carbon..")
        self.reactor_thread.die()
        self.reactor_thread.join()

        #this may be unnecessary
        if remove_pids:
            pids = [os.path.join(self.STORAGEDIR, f) for f in os.listdir(self.STORAGEDIR) if f[-4:]=='.pid']
            for pidfile in pids:
                log.debug("Removing old pidfile %s" % pidfile)
                os.remove(pidfile)
        log.debug("Stopped Carbon.")

    def is_active(self):

        result = True

        if not self.reactor_thread.isAlive(): return False

        for ar in self.application_runners:
            dtype = ar.config['originalname'][7:]
            pickleport = self.configuration.get(dtype,'PICKLE_RECEIVER_PORT')
            result = result and waitforsocket('localhost',pickleport, 2, 1, 1)

        return result

    def print_status(self):
        """
        Prints the reactor status followed by a list of linked applications
        and any ports or connections that are currently controlled by the
        reactor.
        """

        print('Reactor Status:')

        print('  Running: %s' % str(reactor.running))
        print('  Started: %s' % str(reactor._started))
        print('  Stopped: %s' % str(reactor._stopped))

        print('%d Application Runners' % len(self.application_runners))
        for ar in self.application_runners:
            print('  %s' % ar.config['originalname'])

        readers = reactor.getReaders()
        listen_ports = [r.port for r in readers if r.__class__.__name__ == 'Port']
        print('%d Open Ports' % len(listen_ports))
        for p in listen_ports:
            print('  %d' % p)

        outbound_connections = [r for r in readers if r.__class__.__name__ == 'Client']
        print('%d Outbound Connections' % len(outbound_connections))
        for c in outbound_connections:
            host = c.getHost()
            peer = c.getPeer()
            print('  %s:%d->%s:%d(%s)' % ("localhost", host.port, peer.host, peer.port, peer.type))

        inbound_connections = [r for r in readers if r.__class__.__name__ == 'Server']
        print('%d Inbound Connections' % len(inbound_connections))
        for c in inbound_connections:
            print('  %s:%d<-%s:%d(%s)' % ("localhost", c.server.port, c.client[0], c.client[1], c.server._type))


    class ReactorThread(threading.Thread):
        def run(self):
            reactor.run(False)

        def die(self):
            reactor.callFromThread(reactor.stop)

