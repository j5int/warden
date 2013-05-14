# -*- coding: utf-8 -*-

from raven import Client
import time
import os
import email
import json
import string
import sys
from datetime import datetime
import dateutil.parser
from imaplib import IMAP4_SSL, IMAP4
from warden.warden_logging import log
import ConfigParser

class SentryEmailProcessor(object):
    NAME = "sentry"
    EMAIL_SUBJECT_IDENTIFIER = "sentry"

    def __init__(self, config):
        self.client = Client(config['sentry_dsn'])
        self.validation_key = config['email_body_validation_key']

    def process(self, message):
        """Takes a mail message, parses the relevant part, and sends the parsed
        data to Sentry using the Raven client.

        The message must be a multipart message with a 'text/plain' part. This 'text/plain'
        part must begin with the correct sentry validation key, followed by json data.
        If the message is not in this format, it will be dropped."""

        raised = False

        # If message is multipart we only want the text version of the body,
        # this walks the message and gets the body.
        # multipart means dual html and text representations
        if message.get_content_maintype() == 'multipart':
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    # Check if this is the relevant part of the message
                    if body.startswith(self.validation_key):
                        json_ = self.parse_json_message(body[self.validation_key.__len__()+1:])
                        self.raise_to_sentry(json_)
                        raised = True
                        break
        if not raised:
            log.warning("Message is not in the correct format to be processed by SentryEmailProcessor, even though it's subject line indicates that it ought to be. Dropping mail.")

    def raise_to_sentry(self, jsondata):
        try:
            event_date = dateutil.parser.parse(jsondata['date'])
        except Exception:
            event_date = datetime.utcnow()

        event_data = jsondata['data']
        event_data['server_name'] = jsondata['server_name']

        self.client.capture('Exception', message = jsondata['message'], date = event_date, data = event_data)

    def parse_json_message(self, text):
        text = text.replace('\r\n ', '\n')
        text = text.replace('\n', '')
        parsed_data = json.loads(text)
        return parsed_data

class CarbonEmailProcessor(object):
    NAME = "carbon"
    EMAIL_SUBJECT_IDENTIFIER = "j5_parsable"

    def __init__(self, config):
        self.config = config

    def process(self, message):
        """Takes a mail message with one or more attachments and stores the attachments
        in a directory specified by config['whispher_storage_path']

        The message must be a multipart message with a 'text/plain' part and one or more attachments.
        The 'text/plain' part must begin with the correct carbon validation key.
        If the message is not in this format, it will be dropped."""

        whisper_file_handled = False

        # If message is multipart we only want the text version of the body,
        # this walks the message and gets the body.
        # multipart means dual html and text representations
        if message.get_content_maintype() == 'multipart':
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    # Check if this is the relevant part of the message
                    if body.startswith(self.config['email_body_validation_key']):
                        # Re-walk the parts to retrieve the attachments
                        for p in message.walk():
                            if p.get('Content-Disposition') is None or p.get_content_maintype() == 'multipart':
                                continue

                            filename = p.get_filename()
                            file_data = p.get_payload(decode=True)
                            self.handle_whisper_file(filename, file_data)

                            whisper_file_handled = True
                        break
        if not whisper_file_handled:
            log.warning("Message is not in the correct format to be processed by CarbonEmailProcessor, even though it's subject line indicates that it ought to be. Dropping mail.")


    def handle_whisper_file(self, filename, file_data):
        path = os.path.join(self.config['whisper_storage_path'], self.filename_to_path(filename))
        name = self.get_real_filename(filename)
        full_name = os.path.join(path, name)

        if not os.path.isdir(path):
            os.makedirs(path)

        file = open(full_name, 'w')
        file.write(file_data)
        file.close

    def filename_to_path(self, filename):
        return os.path.join(*(filename.split('.')[:-2] or ['']))

    def get_real_filename(self, filename):
        return '.'.join(filename.split('.')[-2:])

class IMAPReceiver(object):
    def __init__(self, config):
        self.config = config
        if config.get('email', 'use_ssl'):
            self.imap4 = IMAP4_SSL
        else:
            self.imap4 = IMAP4
        self.sentry_processor = SentryEmailProcessor(dict(config.items('sentry')))
        self.carbon_processor = CarbonEmailProcessor(dict(config.items('carbon')))
        self.processors = [self.sentry_processor, self.carbon_processor]
        self.connected = False

    def start(self):

        # Try to connect to mailbox until successful
        while True:
            try:
                self.connection = self.connect_to_mailbox()
                self.connected = True
                resp, data = self.connection.select('INBOX')

                if resp != "OK":
                    raise "The INBOX mailbox does not exist."

                # Continually check for new mails (with sleep time specified in settings.py)
                while True:
                    self.check_mails()
                    time.sleep(self.config.get('daemon','recheck_delay'))
            except Exception as e:
                log.error(e)
            finally:
                if self.connected:
                    self.connection.logout()
                time.sleep(self.config.get('daemon','recheck_delay'))

    def connect_to_mailbox(self):
        connection = self.IMAP4(self.config.get('email','email_host'))
        connection.login(self.config.get('email','email_username'), self.config.get('email','email_password'))
        return connection

    def check_mails(self):
        for processor in self.processors:
            log.info("Checking for new mails for the %s email processor", processor.NAME)

            typ, msg_ids = self.connection.search(None, '(SUBJECT "%s" UNSEEN)' % processor.EMAIL_SUBJECT_IDENTIFIER)

            msg_ids = msg_ids[0].strip()

            log.debug("msg_ids=%r", msg_ids)

            if len(msg_ids) > 0:
                log.info("Fetching %d mails..", len(msg_ids.split(' ')))
                msg_ids = string.replace(msg_ids, ' ', ',')
                typ, msg_data = self.connection.fetch(msg_ids, '(RFC822)')
                log.info("Fetched. Now processing..")

                for response_part in msg_data:
                    # A response part is either a string '(stuff here)' or a tuple: ('stuff here', 'stuff here')
                    # We only want the tuples, these are actual messages.

                    if isinstance(response_part, tuple):
                        msg = email.message_from_string(response_part[1])
                        log.info("Processing message: %r", response_part[0])
                        processor.process(msg)
            else:
                log.info("No new messages.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Warden IMAPReceiver configuration file parser')
    parser.add_argument('--config', help="Path to the Warden IMAPReceiver configuration file.", dest='config')
    parser.add_argument('--server', help='Run continually in server mode (default is to run once)', action='store_true', default=False)
    args, unknown  = parser.parse_known_args(sys.argv)
    imapreceiver_configuration_file = os.path.abspath(os.path.expanduser(args.config))
    if not os.path.exists(imapreceiver_configuration_file):
        log.error('The IMAPReceiver config file specified ("%s") does not exist!' % imapreceiver_configuration_file)
        sys.exit(1)
    config = ConfigParser.SafeConfigParser()
    config.read(imapreceiver_configuration_file)
    imapreceiver = IMAPReceiver(config)
    if args.server:
        imapreceiver.start()
    else:
        imapreceiver.connect_to_mailbox()
        imapreceiver.check_mails()

