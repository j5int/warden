import os
import time
from socket import socket
import random
from warden_carbon import CarbonManager
from warden_gentry import GentryManager
from warden_diamond import DiamondManager

class Warden:

    def __init__(self, carbon_config_file, daemons, gentry_settings_arg, diamond_config_file):

        print('Starting Warden\n----------------')
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

        self.carbon = CarbonManager(carbon_config_file, daemons=daemons)

        self.gentry = GentryManager(gentry_settings_arg)
        self.gentry.initialise()

        self.diamond = DiamondManager(diamond_config_file)


    def startup(self):

        self.carbon.start_daemons()
        while not self.carbon.is_active():
            time.sleep(0.5)
        print('Carbon started')

        self.gentry.start()
        while not self.gentry.is_active():
            time.sleep(0.5)
        print('Gentry started')

        self.diamond.start()


    def is_active(self):

        result = self.gentry.is_active()

        if result == True:
            result = self.carbon.is_active()

        if result == True:
            result = self.diamond.is_active()

        return result

    def shutdown(self):
        self.diamond.stop()
        self.gentry.stop()
        self.carbon.stop_daemons()


def main():
    carbon_config = '/home/benm/.graphite/conf/carbon.conf'

    carbon_daemons =    [
                            CarbonManager.CACHE,
                            CarbonManager.AGGREGATOR
                        ]

    gentry_settings = 'gentry.settings'

    diamond_config_file = '/home/benm/.diamond/etc/diamond/diamond.conf'

    warden = Warden(carbon_config, carbon_daemons, gentry_settings, diamond_config_file)

    warden.startup()

    while not warden.is_active():
        time.sleep(0.5)
    print('Ready')

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        pass

    warden.shutdown()


if __name__ == '__main__':
    main()
