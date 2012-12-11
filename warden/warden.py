import os
import time
from warden_utils import waitforsocket
from warden_carbon import CarbonManager
from warden_gentry import GentryManager

class Warden:

    def __init__(self, carbon_config_file, daemons, gentry_settings_arg):

        # check for config file existings
        try:
            if os.path.isfile(carbon_config_file):
                with open(carbon_config_file) as a:
                    pass
        except IOError as e:
            raise e

        self.carbon = CarbonManager(carbon_config_file)
        for d in daemons:
            self.carbon.add_daemon(d)

        self.gentry = GentryManager(gentry_settings_arg)

    def startup(self):

        self.gentry.start()
        while not self.gentry.is_active():
            time.sleep(0.5)
        print('Gentry started')

        self.carbon.start_daemons()
        while not self.carbon.is_active():
            time.sleep(0.5)
        print('Carbon started')


    def is_active(self):

        result = self.gentry.is_active()

        if result == True:
            result = self.carbon.is_active()

        return result

    def shutdown(self):
        self.carbon.stop_daemons()
        self.gentry.stop()

if __name__ == '__main__':

    carbon_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test', 'conf', 'carbon.conf')

    carbon_daemons =    [
                            CarbonManager.CACHE,
                            CarbonManager.AGGREGATOR
                        ]

    gentry_settings = 'gentry.settings'

    warden = Warden(carbon_config, carbon_daemons, gentry_settings)

    warden.startup()

    while not warden.is_active():
        time.sleep(0.5)
    print('Ready')

    time.sleep(60)

    warden.shutdown()

