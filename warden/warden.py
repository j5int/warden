import sys
import time
from warden_carbon import CarbonManager
from warden_gentry import GentryManager
from warden_diamond import DiamondManager
from warden_logging import log
from warden_utils import StartupException
import datetime

class Warden:
    """
    Warden is a solution for controlling Carbon daemons, Sentry, Graphite-web and Diamond all within a single process.
    The sub systems all run in separate threads and can be shutdown gracefully using sigint or stop commands.
    """

    def __init__(self,
                 new_graphite_root=None,            # does the graphite root variable need to be changed
                 carbon_config_path=None,           # where are the carbon config files
                 diamond_config_path=None,          # where is the diamond config file
                 gentry_settings_path=None,       # the name of the gentry settings module
                 sentry_key_path=None               # a path to a file containing the sentry private key (?) this
                                                    # this overrides the value in the gentry_settings_module
    ):
        """
        Warden uses values from its default settings file UNLESS explicitely defined
        here in the constructor.
        """
        import settings

        self.settings = settings
        self.startuptime = None
        self.shutdowntime = None

        # pull new config values into settings object
        if new_graphite_root is not None:
            self.settings.GRAPHITE_ROOT = new_graphite_root
        if carbon_config_path is not None:
            self.settings.CARBON_CONFIG = carbon_config_path
        if diamond_config_path is not None:
            self.settings.DIAMOND_CONFIG = diamond_config_path
        if gentry_settings_path is not None:
            self.settings.GENTRY_SETTINGS_PATH = gentry_settings_path
        if sentry_key_path is not None:
            self.settings.SENTRY_KEY_FILE = sentry_key_path

        log.info('Initialising Warden..')
        try:
            # initialise Carbon, daemon services are setup here, but the event reactor is not yet run
            self.carbon = CarbonManager(self.settings)

            # initialise Gentry, this will also perform database manipulation for Sentry
            self.gentry = GentryManager(self.settings)

            # initialise Diamond, not much is required here
            self.diamond = DiamondManager(self.settings)
        except Exception:
            log.exception("An error occured during initialisation.")
            sys.exit(1)

    def startup(self):
        """
        Start the warden instance
        Carbon, Diamond and Gentry are started in order, and this method will only exit once all are bound to their
        correct ports
        """

        log.info('Starting Warden..')
        try:
            self.carbon.start()
            self.wait_for_start(self.carbon)
            log.debug('1. Carbon Started')

            self.diamond.start()
            self.wait_for_start(self.diamond)
            log.debug('2. Diamond Started')

            self.gentry.start()
            self.wait_for_start(self.gentry)
            log.debug('3. Gentry Started')

            # blocking
            log.info('Started Warden.')
            self.startuptime = datetime.datetime.now()

        except Exception, e:
            raise StartupException(e)

    def wait_for_start(self, process):
        while not process.is_active():
            time.sleep(0.5)

    def is_active(self):
        """
        A general active state query.
        returns False as soon as anything is not running
        """
        result = self.gentry.is_active()

        if result:
            result = self.carbon.is_active()

        if result:
            result = self.diamond.is_active()

        return result

    def shutdown(self):
        """
        Shutdown in order, some threading may be wrong here, make sure of inidividual .join()
        """
        self.shutdowntime = datetime.datetime.now()

        elapsed = self.shutdowntime - self.startuptime
        log.info('Warden was active for %s' % str(elapsed))

        log.info('Shutting down Warden..')

        try:
            self.gentry.stop()
            log.debug('3. Gentry Stopped.')
        except Exception:
            log.exception("An error occured while shutting down Gentry")

        try:
            self.diamond.stop()
            log.debug('2. Diamond Stopped.')
        except Exception:
            log.exception("An error occured while shutting down Diamond")

        try:
            self.carbon.stop()
            log.debug('1. Carbon Stopped.')
        except Exception:
            log.exception("An error occured while shutting down Carbon")

        log.info('Shut down Warden.')

    def start(self):
        try:
            self.startup()
            while True:
                time.sleep(5)
                if not self.is_active():
                    log.error("Something caused one of the services to stop!")
                    break
                # need some way to pickup errors at runtime. should check after each sleep whether any of the
                # services have picked up an error

        except KeyboardInterrupt:
            log.info("Keyboard interrupt received.")
            self.shutdown()
        except StartupException:
            log.exception("An error occured during startup.")
            self.shutdown()
        except Exception:
            log.exception("An error occured while running.")
            self.shutdown()

def main():
    warden = Warden()

    warden.start()


if __name__ == '__main__':
    main()
