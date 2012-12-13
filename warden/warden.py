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

    def __init__(self, carbon_config_file, daemons, gentry_settings_arg, diamond_config_file):
        """
        Constructor takes arguments:
        carbon_config_file:             a path to the carbon config file
        daemons:                        an array of carbon daemons (see warden_carbon for details)
        gentry_settings_arg:            path to the gentry settings.py module
        diamond_config_file:            a path to a diamond configuration file
        """

        log.info('Initialising Warden..')
        # check for config file existings
        try:
            if os.path.isfile(carbon_config_file):
                with open(carbon_config_file) as a:
                    pass
            if os.path.isfile(diamond_config_file):
                with open(diamond_config_file) as a:
                    pass
        except IOError as e:
            raise e

        # initialise Carbon, daemon services are setup here, but the event reactor is not yet run
        self.carbon = CarbonManager(carbon_config_file, daemons=daemons)

        # initialise Gentry, this will perform database manipulation for Sentry
        self.gentry = GentryManager(gentry_settings_arg)

        # initialise Diamond, not much is required here
        self.diamond = DiamondManager(diamond_config_file)

    def startup(self):
        """
        Start the warden instance
        Carbon, Diamond and Gentry are started in order, and this method will only exit once all are bound to their
        correct ports
        """

        log.info('Starting Warden..')

        self.carbon.start_daemons()
        while not self.carbon.is_active():
            time.sleep(0.5)
        log.info('1. Carbon Started')

        self.diamond.start()
        while not self.diamond.is_active():
            time.sleep(0.5)
        log.info('2. Diamond Started')

        self.gentry.start()
        while not self.gentry.is_active():
            time.sleep(0.5)
        log.info('3. Gentry Started')

        # blocking
        while not self.is_active():
            time.sleep(0.5)
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

    def shutdown(self):
        """
        Shutdown in order, some threading may be wrong here, make sure of inidividual .join()
        """

        log.info('Shutting down Warden..')

        self.diamond.stop()
        self.gentry.stop()
        self.carbon.stop_daemons()

        log.info('Shut down Warden.')


def main():
    """
    TEST CODE:
    ideally all paths should be loaded from a config file and NOT hardcoded like this
    """
    carbon_config = '/home/benm/.graphite/conf/carbon.conf'

    carbon_daemons =    [
                            CarbonManager.CACHE,
                            CarbonManager.AGGREGATOR
                        ]

    gentry_settings = 'gentry.settings'

    diamond_config_file = '/home/benm/.diamond/etc/diamond/diamond.conf'

    if platform.system() == 'Windows':
        carbon_config = 'C:\\Graphite\conf\carbon.conf'
        diamond_config_file = 'C:\\.diamond/diamond.conf'

    warden = Warden(carbon_config, carbon_daemons, gentry_settings, diamond_config_file)

    warden.startup()


    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        pass

    warden.shutdown()


if __name__ == '__main__':
    main()
