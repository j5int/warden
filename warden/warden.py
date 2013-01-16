import os
import sys
import time
import platform
from warden_carbon import CarbonManager
from warden_gentry import GentryManager
from warden_diamond import DiamondManager
from warden_logging import log


class Warden:
    """
    Warden is a solution for controlling Carbon daemons, Sentry, Graphite-web and Diamon all within a single process.
    The sub systems all run in separate threads and can be shutdown gracefully using sigint or stop commands.
    """

    def __init__(self,
                 new_graphite_root=None,            # does the graphite root variable need to be changed
                 carbon_config_file=None,           # where are the carbon config files
                 diamond_config_file=None,          # where is the diamond config file
                 gentry_settings_module=None        # the name of the gentry settings module
    ):
        """
        Warden uses values from its default settings file UNLESS explicitely defined
        here in the constructor.
        """
        import settings

        self.settings = settings

        # pull new config values into settings object
        if new_graphite_root is not None:
            self.settings.GRAPHITE_ROOT = new_graphite_root
        if carbon_config_file is not None:
            self.settings.CARBON_CONFIG = carbon_config_file
        if diamond_config_file is not None:
            self.settings.DIAMOND_CONFIG = diamond_config_file
        if gentry_settings_module is not None:
            self.settings.GENTRY_SETTINGS_MODULE = gentry_settings_module

        log.info('Initialising Warden..')

        # initialise Carbon, daemon services are setup here, but the event reactor is not yet run
        self.carbon = CarbonManager(self.settings)

        # initialise Gentry, this will also perform database manipulation for Sentry
        self.gentry = GentryManager(self.settings)

        # initialise Diamond, not much is required here
        self.diamond = DiamondManager(self.settings)

    def startup(self):
        """
        Start the warden instance
        Carbon, Diamond and Gentry are started in order, and this method will only exit once all are bound to their
        correct ports
        """

        log.info('Starting Warden..')

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

    def wait_for_start(self, process):
        while not process.is_active():
            time.sleep(0.5)


    def shutdown(self):
        """
        Shutdown in order, some threading may be wrong here, make sure of inidividual .join()
        """

        log.info('Shutting down Warden..')

        self.diamond.stop()
        log.debug('3. Diamond Stopped.')

        self.gentry.stop()
        log.debug('2. Gentry Stopped.')

        self.carbon.stop()
        log.debug('1. Carbon Stopped.')

        log.info('Shut down Warden.')


def main():
    warden = Warden()

    try:
        warden.startup()
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        warden.shutdown()


if __name__ == '__main__':
    main()
