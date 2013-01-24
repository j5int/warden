import threading
import re
import os
import smtplib
import time
from smtplib import SMTP
from smtp_forwarder import BaseMailGenerator
from warden_logging import log
from  smtp_forwarder import GraphiteMailGenerator


class SMTPForwarderManager:

    def __init__(self, s):
        self.settings = s
        self.dispatcherThread = self.CentralDispatcherThread(self.settings)

    def start(self):
        log.debug('Starting Graphite SMTP forwader...')
        self.dispatcherThread.start()
        log.debug('Started Graphite SMTP forwader.')

    def stop(self):
        log.debug('Stopping Graphite SMTP forwader...')
        self.dispatcherThread.stop()
        log.debug('Stopped Graphite SMTP forwader.')

    class CentralDispatcherThread(threading.Thread):

        def __init__(self, s):
            threading.Thread.__init__(self)
            self.running = False
            self.settings = s
            self.settings.METRIC_PATTERNS_TO_SEND = self.compile_metric_patterns(self.settings.METRIC_PATTERNS_TO_SEND)
            print self.settings.METRIC_PATTERNS_TO_SEND

        def compile_metric_patterns(self, old_patterns):

            compiled = []
            for p in old_patterns:
                if p.endswith('.wsp'):
                    p = p[:-4]
                p = p.replace('.', os.path.sep).replace('\\','\\\\').replace('*','.+')
                p = ".*%s\\.wsp$" % p
                compiled.append(re.compile(p))

            return compiled

        def run(self):
            self.running = True
            self.SLEEP_TIME = 30
            self.last_poll_time = time.time()

            while self.running:
                if time.time()-self.last_poll_time < self.SLEEP_TIME:
                    time.sleep(1)
                    continue

                conn = SMTP()
                try:
                    log.debug('Connecting...')
                    conn.connect(self.settings.EMAIL_HOST)
                    conn.set_debuglevel(False)

                    if self.settings.EMAIL_USE_TLS:
                        conn.starttls()

                    log.debug('Logging in..')
                    conn.login(self.settings.EMAIL_USERNAME, self.settings.EMAIL_PASSWORD)
                    max_mail_size = int(conn.esmtp_features['size'])

                    for generator_cls in BaseMailGenerator.generator_registry:
                        generator = generator_cls(self.settings, max_mail_size)
                        mails = generator.get_mail_list()

                        for mail in mails:
                            if mail:
                                log.debug('Sending mail..')
                                log.debug('FROM: ' + mail['From'])
                                log.debug('TO: ' + mail['To'])
                                log.debug('SIZE: ' + str(len(mail.as_string())))

                                start_time = time.time()
                                conn.sendmail(mail['From'], mail['To'], mail.as_string())
                                log.debug('Sent mail in %d seconds.' % (time.time()-start_time))

                    self.last_poll_time = time.time()
                except smtplib.SMTPRecipientsRefused:
                    log.error('STMPRecipientsRefused')
                except smtplib.SMTPHeloError:
                    log.error('SMTPHeloError')
                except smtplib.SMTPSenderRefused:
                    log.exception('SMTPSenderRefused')
                except smtplib.SMTPDataError:
                    log.error('SMTPDataError')
                except Exception as exc:
                    log.exception('An exception occured when sending mail')
                finally:
                    if time.time() - self.last_poll_time < self.SLEEP_TIME:
                        # Try send again in 10 minutes instead of retrying the instant it fails.
                        self.last_poll_time = time.time() - self.SLEEP_TIME + (60 * 10)

                    if hasattr(conn, 'sock') and conn.sock:
                        conn.quit()

        def stop(self):
            self.running = False