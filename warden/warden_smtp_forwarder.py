import threading
import re
import os
import smtplib
import time
from smtplib import SMTP
from smtp_forwarder import BaseMailGenerator
from warden_logging import log
import ConfigParser


class SMTPForwarderManager:

    def __init__(self, config_file):

        config_file = os.path.expandvars(os.path.expanduser(config_file))

        self.dispatcherThread = self.CentralDispatcherThread(config_file)

    def start(self):
        log.debug('Starting Graphite SMTP forwader...')
        self.dispatcherThread.start()
        log.debug('Started Graphite SMTP forwader.')

    def stop(self):
        log.debug('Stopping Graphite SMTP forwader...')
        self.dispatcherThread.stop()
        log.debug('Stopped Graphite SMTP forwader.')

    class CentralDispatcherThread(threading.Thread):

        def __init__(self, config_file):
            threading.Thread.__init__(self)
            self.running = False
            self.config_file = config_file
            self.busy_sending = False


        def prettiertime(self, s):
            if s <60:
                return '%d seconds' % s
            if s < 3600:
                min = s / 60
                return '%d minutes' % min
            hour = s / 3600
            return '%d hours' % hour

        def run(self):
            self.running = True

            self.configuration = self.load_config()

            self.SLEEP_TIME = int(self.configuration['send_interval'])
            self.last_poll_time = time.time()

            log.debug('SMTP dispatch will occur in %s' % str(self.prettiertime(self.SLEEP_TIME)))

            while self.running:
                if (time.time()-self.last_poll_time) < self.SLEEP_TIME:
                    time.sleep(1)
                    continue
                                                    # this overrides the value in the gentry_settings_module

                conn = SMTP()
                try:
                    log.debug('Connecting...')
                    conn.connect(self.configuration['email_host'])
                    conn.set_debuglevel(False)

                    if self.configuration['email_use_tls']:
                        conn.starttls()

                    log.debug('Logging in..')
                    conn.login(self.configuration['email_username'], self.configuration['email_password'])
                    max_mail_size = int(conn.esmtp_features['size'])

                    for generator_cls in BaseMailGenerator.generator_registry:
                        generator = generator_cls(self.configuration, max_mail_size)
                        mails = generator.get_mail_list()

                        for mail in mails:
                            if mail:

                                bytes = len(mail.as_string())
                                if bytes < 1024:
                                    sizestr = str(bytes) + "b"
                                elif bytes < 1048576:
                                    sizestr = "%.2f Kb" % (bytes/1024.0)
                                else:
                                    sizestr = "%.2f Mb" % ((bytes/1024.0)/1024.0)

                                log.debug('%s: Sending mail to: %s Size: %s' % (generator.__class__.__name__, mail['To'],sizestr))

                                start_time = time.time()
                                conn.sendmail(mail['From'], mail['To'], mail.as_string())
                                log.debug('Sent mail in %d seconds.' % (time.time()-start_time))

                    self.last_poll_time = time.time()

                    self.configuration = self.load_config()
                    self.SLEEP_TIME = int(self.configuration['send_interval'])

                    log.debug('Next SMTP dispatch will occur in %s' % str(self.prettiertime(self.SLEEP_TIME)))

                except smtplib.SMTPRecipientsRefused:
                    log.error('STMPRecipientsRefused')
                except smtplib.SMTPHeloError:
                    log.error('SMTPHeloError')
                except smtplib.SMTPSenderRefused:
                    log.exception('SMTPSenderRefused')
                except smtplib.SMTPDataError:
                    log.error('SMTPDataError')
                except Exception:
                    log.exception('An exception occured when sending mail')
                finally:
                    # Did it fail to send
                    if time.time() - self.last_poll_time > self.SLEEP_TIME:
                        self.last_poll_time = time.time() + (60 * 10) - self.SLEEP_TIME
                        log.debug('Next SMTP dispatch will occur in %s' % str(self.prettiertime(60*10)))

                    if hasattr(conn, 'sock') and conn.sock:
                        conn.quit()

        def stop(self):
            self.running = False

        def compile_metric_pattern(self, p):

                if p.endswith('.wsp'):
                    p = p[:-4]
                p = p.replace('.', os.path.sep).replace('\\','\\\\').replace('*','.+')
                p = ".*%s\\.wsp$" % p

                return re.compile(p)

        def load_config(self):
            self.cfg = ConfigParser.RawConfigParser()
            self.cfg.read(self.config_file)

            self.configuration = {}
            for section in self.cfg.sections():
                for option in self.cfg.options(section):
                    self.configuration[option] = self.cfg.get(section, option)

            patternsstring = self.configuration['metric_patterns_to_send']
            patterns = patternsstring.split(',')
            compiled_patterns = []
            for pattern in patterns:
                if len(pattern.strip())>0:
                    compiled_patterns.append(self.compile_metric_pattern(pattern.strip()))

            self.configuration['metric_patterns_to_send'] = compiled_patterns

            return self.configuration