import os
import time
from warden_utils import waitforsocket
from warden_carbon import CarbonManager
from warden_sentry import SentryManager

class Warden:

    def __init__(self, carbon_config_file, daemons, sentry_config_file):

        # check for config file existings
        try:
            if os.path.isfile(carbon_config_file):
                with open(carbon_config_file) as a:
                    pass
            if os.path.isfile(sentry_config_file):
                with open(sentry_config_file) as b:
                    pass
        except IOError as e:
            raise e

        self.carbon = CarbonManager(carbon_config_file)
        for d in daemons:
            self.carbon.add_daemon(d)

        self.sentry = SentryManager(sentry_config_file, overwrite=False)

    def startup(self):
        self.sentry.start_sentry()

        self.carbon.start_daemons()


    def is_active(self):

        result = self.sentry.is_active()

        if result == True:
            result = self.carbon.is_active()

        return result

    def shutdown(self):
        self.carbon.stop_daemons()
        self.sentry.stop_sentry()

if __name__ == '__main__':

    carbon_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test', 'conf', 'carbon.conf')

    carbon_daemons =    [
                            CarbonManager.CACHE,
                            CarbonManager.AGGREGATOR
                        ]

    sentry_config = '/home/benm/.sentry/sentry.conf.py'

    warden = Warden(carbon_config, carbon_daemons, sentry_config)

    warden.startup()

    while not warden.is_active():
        time.sleep(0.5)
    print('Ready')

    warden.shutdown()

