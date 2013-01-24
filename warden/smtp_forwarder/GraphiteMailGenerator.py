import re
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from warden.warden_logging import log

import BaseMailGenerator

@BaseMailGenerator.register_generator
class GraphiteMailGenerator(BaseMailGenerator.BaseMailGenerator):

    def __init__(self, some_settings, max_mail_size):
        super(GraphiteMailGenerator, self).__init__()
        self.settings = some_settings
        self.storage_dir = os.path.join(os.environ['GRAPHITE_ROOT'], 'storage', 'whisper')
        # Mails must be 10MB or less
        self.max_mail_size = min(max_mail_size, (1024 * 1024 * 10))


    def get_mail_list(self):
        if not self.settings.EMAIL_TO or self.settings.EMAIL_TO == '':
            log.error('No receiver email address defined.')
            return []

        if not os.path.isdir(self.storage_dir):
            log.error('Invalid whisper storage path specified.')
            return []

        mails = []
        current_mail = self._setup_mail()
        current_size = 0
        for attachment_path in self._match_files(self.storage_dir):
            attachment = self.create_attachment(file_path, self._path_to_metric_filename(attachment_path))
            if attachment:
                # Attachments are Base64 encoded and hence, are
                # roughly 137% the size of the actual attachment size,
                # so we need to use this final size.
                file_size = len(attachment.as_string())
                if file_size > self.max_mail_size:
                    self.debug('File size exceeds limit and will not be sent: %s' % file_size)
                if current_size + file_size > self.max_mail_size:
                    mails.append(current_mail)
                    current_mail = self._setup_mail()
                    current_size = 0
                current_mail.attach(attachment)
                current_size += file_size
        if current_size > 0:
            mails.append(current_mail)
        return mails

    def _setup_mail(self):
        mail = MIMEMultipart()
        mail['To'] = self.settings.EMAIL_TO
        mail['From'] = self.settings.EMAIL_FROM
        mail['Subject'] = self.settings.EMAIL_SUBJECT_VALIDATION_KEY
        mail.attach(MIMEText(self.settings.EMAIL_BODY_VALIDATION_KEY))
        return mail

    def _match_files(self, path):
        for possible_file in self._walk_directory(path):
            for patterns in self.settings.METRIC_PATTERNS_TO_SEND:
                if re.match(patterns, possible_file) is not None:
                    log.debug('Found match: ' + possible_file)
                    yield possible_file
                    break

    def _walk_directory(self, path):
        if isinstance(path, str):
            for root, folders, files in os.walk(path):
                for f in self._select_files(root, files):
                    yield f
        elif isinstance(path, list) or isinstance(path, tuple):
            for p in path:
                if not os.path.isdir(p):
                    continue
                for root, folders, files in os.walk(p):
                    for f in self._select_files(root, files):
                        yield f

    def _select_files(self, dir, files):
        for filename in files:
            extension = os.path.splitext(filename)[1].strip()
            if extension == '.wsp':
                yield os.path.join(dir, filename)

    def _path_to_metric_filename(self, full_path):
        relevant_path = full_path[len(self.storage_dir):].strip(os.sep)
        metric_filename = relevant_path.replace(os.sep, '.')
        return metric_filename