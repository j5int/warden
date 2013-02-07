import os
import threading
from warden_utils import waitforsocket, normalize_path
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
from twisted.application import  service
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
        manager.start()

        manager.stop()
    """

    def __init__(self, new_graphite_root=None, carbon_conf_file=None):
        """
        Build the storage directory and prepare for Start. The storage directory
        is in the GRAPHITE_ROOT folder which is used by all of the carbon daemons.
        GRAPHITE_ROOT can be modified as shown by:
            os.environ["GRAPHITE_ROOT"] = some_storage_directory
        """

        log.debug("Initialising Carbon..")

        # If an overriding graphite_root is provided: set os.environ['GRAPHITE_ROOT']
        if new_graphite_root is not None:
            os.environ["GRAPHITE_ROOT"] = normalize_path(new_graphite_root)

        # Log current GRAPHITE_ROOT
        log.debug("GRAPHITE_ROOT = %s" % os.environ['GRAPHITE_ROOT'])

        # If the path to the carbon.conf file is supplied: use it
        if carbon_conf_file is not None:
            self.carbon_config_file = normalize_path(carbon_conf_file)
        else:
            # otherwise build the path using GRAPHITE_ROOT
            self.carbon_config_file = os.path.join(os.environ['GRAPHITE_ROOT'], 'conf','carbon.conf')

        #read config file, used mostly to get the port its running on
        self.configuration = SafeConfigParser()
        self.configuration.read(self.carbon_config_file)

        self.application_service = service.MultiService()
        self.reactor_thread = None


    def start(self):
        log.debug("Starting Carbon..")

        twistd_options = ["--no_save", "--nodaemon", 'carbon-combined']

        if self.carbon_config_file is not None:
            twistd_options.append('--config=' + self.carbon_config_file)

        config = ServerOptions()
        config.parseOptions(twistd_options)
        config.subCommand = 'carbon-combined'

        # Hacky stuff to get carbon logging to the proper place
        from carbon.conf import settings as c_sett
        from carbon import log as c_log

        log_dir = os.path.join(os.environ['GRAPHITE_ROOT'], 'storage', 'log','carbon')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        c_log.logToStdout()
        c_log.logToDir(log_dir)

        # Change these if you want big logs
        c_sett.LOG_UPDATES = False
        c_sett.LOG_CACHE_HITS = True



        plg = config.loadedPlugins[config.subCommand]
        self.application_service = plg.makeService(config.subOptions)

        if reactor.running:
            raise Exception('Reactor is already running.')

        self.application_service.startService()
        self.reactor_thread = self.ReactorThread()
        self.reactor_thread.start()

        log.debug("Started Carbon.")

    def stop(self):
        if self.reactor_thread.isAlive():
            log.debug("Stopping Carbon..")

            self.application_service.stopService()

            self.reactor_thread.die()
            self.reactor_thread.join()

            log.debug("Stopped Carbon.")
        else:
            log.error("Can't stop Carbon/Twistd if it has not started.")

    def is_active(self):
        """
        Carbon-combined is defined as active once the aggregator is ready to receive metrics
        """
        result = True

        if not self.reactor_thread.isAlive(): return False

        pickleport = self.configuration.get('combined','AGGREGATOR_PICKLE_RECEIVER_PORT')
        result = result and waitforsocket('localhost',pickleport, 2, 1, 1)

        return result

    class ReactorThread(threading.Thread):
        def run(self):
            reactor.run(False)

        def die(self):
            reactor.callFromThread(reactor.stop)

