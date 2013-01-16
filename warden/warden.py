import os
import sys
import time
import platform
from warden_carbon import CarbonManager
from warden_gentry import GentryManager
from warden_diamond import DiamondManager
from warden_logging import log
import settings

class Warden:
    """
    Warden is a solution for controlling Carbon daemons, Sentry, Graphite-web and Diamon all within a single process.
    The sub systems all run in separate threads and can be shutdown gracefully using sigint or stop commands.
    """

    def __init__(self, settings):
        """

        """
        self.settings = settings

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
        while not self.carbon.is_active():
            time.sleep(0.5)
        log.debug('1. Carbon Started')

        self.diamond.start()
        while not self.diamond.is_active():
            time.sleep(0.5)
        log.debug('2. Diamond Started')

        self.gentry.start()
        while not self.gentry.is_active():
            time.sleep(0.5)
        log.debug('3. Gentry Started')

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
        log.debug('3. Diamond Stopped.')

        self.gentry.stop()
        log.debug('2. Gentry Stopped.')

        self.carbon.stop()
        log.debug('1. Carbon Stopped.')

        log.info('Shut down Warden.')


def main():


    warden = Warden(settings)

    try:

        warden.startup()
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        warden.shutdown()


if __name__ == '__main__':
    main()
