import sys
import os
import time
import ConfigParser
import logging
from warden_carbon import CarbonManager
from warden_gentry import GentryManager
from warden_diamond import DiamondManager
from warden_smtp_forwarder import SMTPForwarderManager
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
                 gentry_settings_path=None,         # the name of the gentry settings module
                 start_stmp_forwarder=True,
                 smtp_forwarder_config_path=None,
                 warden_configuration_file=None

    ):
        """
        Load configuration object
        """
        # If run as main, there must be a config option
        if __name__ == '__main__':
            import argparse
            parser = argparse.ArgumentParser(description='Warden configuration file parser')
            parser.add_argument('--config', help="Path to the Warden configuration file.", dest='config', required=True)
            args, unknown  = parser.parse_known_args(sys.argv)
            warden_configuration_file = os.path.abspath(os.path.expanduser(args.config))
            try:
                with open(warden_configuration_file) as f: pass
            except IOError:
                log.error('"%s" Does Not Exist!' % warden_configuration_file)
                sys.exit(1)

        # Otherwise there may be a config argument
        else:
            if warden_configuration_file is None:
                log.critical('No Warden configuration file supplied! Please use the "warden_configuration_file" parameter.')
                sys.exit()

            warden_configuration_file = os.path.abspath(os.path.expanduser(warden_configuration_file))
            warden_configuration_file = os.path.abspath(os.path.expanduser(args.config))
            try:
                with open(warden_configuration_file) as f: pass
            except IOError:
                log.error('"%s" Does Not Exist!' % warden_configuration_file)
                raise

        self.configuration = ConfigParser.RawConfigParser()
        self.configuration.read(warden_configuration_file)

        # Setup logger
        # this is the stdout log level
        loglevel = getattr(logging, self.configuration.get('warden','loglevel'))
        log.setLevel(loglevel)

        self.startuptime = None
        self.shutdowntime = None

        # pull new config values into configuration object

        if new_graphite_root is not None:
            self.configuration.set('carbon', 'graphite_root', str(new_graphite_root))

        if carbon_config_path is not None:
            self.configuration.set('carbon', 'configuration', str(carbon_config_path))

        if diamond_config_path is not None:
            self.configuration.set('diamond', 'configuration', str(diamond_config_path))

        if gentry_settings_path is not None:
            self.configuration.set('gentry', 'gentry_settings_py_path', str(gentry_settings_path))

        if start_stmp_forwarder is False:
            self.configuration.set('smtp_forwarder', 'enabled', str(start_stmp_forwarder))

        if smtp_forwarder_config_path is not None:
            self.configuration.set('smtp_forwarder', 'configuration', str(smtp_forwarder_config_path))

        log.info('Initialising Warden..')
        try:
            # initialise Carbon, daemon services are setup here, but the event reactor is not yet run
            self.carbon = CarbonManager(
                self.configuration.get('carbon', 'graphite_root'),
                self.configuration.get('carbon', 'configuration'))

            # initialise Gentry, this will also perform database manipulation for Sentry
            self.gentry = GentryManager(
                self.configuration.get('gentry', 'gentry_settings_py_path'))

            # initialise Diamond, not much is required here
            self.diamond = DiamondManager(
                self.configuration.get('diamond', 'diamond_root'),
                self.configuration.get('diamond', 'configuration'),
                getattr(logging, self.configuration.get('diamond','loglevel')))

            if self.configuration.getboolean('smtp_forwarder', 'enabled'):
                self.smtpforward = SMTPForwarderManager(self.configuration.get('smtp_forwarder', 'configuration'))

        except Exception:
            log.exception("An error occured during initialisation.")
            sys.exit(1)

    def _startup(self):
        """
        Start the warden instance
        Carbon, Diamond and Gentry are started in order, and this method will only exit once all are bound to their
        correct ports
        """

        log.info('Starting Warden..')
        try:
            self.carbon.start()
            self._wait_for_start(self.carbon)
            log.debug('1. Carbon Started')

            self.diamond.start()
            self._wait_for_start(self.diamond)
            log.debug('2. Diamond Started')

            self.gentry.start()
            self._wait_for_start(self.gentry)
            log.debug('3. Gentry Started')

            if self.configuration.getboolean('smtp_forwarder', 'enabled'):
                self.smtpforward.start()
                log.debug('4. Graphite SMTP forwarder Started')

            # blocking
            log.info('Started Warden.')
            self.startuptime = self.shutdowntime = datetime.datetime.now()

        except Exception, e:
            raise StartupException(e)

    def _wait_for_start(self, process):
        while not process.is_active():
            time.sleep(0.5)

    def _is_active(self):
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

    def _shutdown(self):
        """
        Shutdown in order, some threading may be wrong here, make sure of inidividual .join()
        """
        self.shutdowntime = datetime.datetime.now()

        elapsed = self.shutdowntime - self.startuptime
        log.info('Warden was active for %s' % str(elapsed))

        log.info('Shutting down Warden..')

        if self.configuration.getboolean('smtp_forwarder', 'enabled'):
            try:
                self.smtpforward.stop()
                log.debug('4. Graphite SMTP forwarder stopped')
            except Exception:
                log.exception('An error occured while shutting down Graphite SMTP forwarder')

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
            self._startup()
            while True:
                time.sleep(5)
                if not self._is_active():
                    log.error("Something caused one of the services to stop!")
                    break
                # need some way to pickup errors at runtime. should check after each sleep whether any of the
                # services have picked up an error

        except KeyboardInterrupt:
            log.info("Keyboard interrupt received.")
            self._shutdown()
        except StartupException:
            log.exception("An error occured during startup.")
            self._shutdown()
        except Exception:
            log.exception("An error occured while running.")
            self._shutdown()

def main():
    warden = Warden()

    warden.start()


if __name__ == '__main__':
    main()
