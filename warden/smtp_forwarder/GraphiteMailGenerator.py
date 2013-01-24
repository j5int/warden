import re
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import BaseMailGenerator

@BaseMailGenerator.register_generator
class GraphiteMailGenerator(BaseMailGenerator.BaseMailGenerator):

    def __init__(self, some_settings):
        super(GraphiteMailGenerator, self).__init__()
        self.settings = some_settings
        self.storage_dir = os.path.join(os.environ['GRAPHITE_ROOT'], 'storage', 'whisper')

    def create_mail(self):
        if not self.settings.EMAIL_TO or self.settings.EMAIL_TO == '':
            print 'No receiver email address defined.'
            return None

        if not os.path.isdir(self.storage_dir):
            print 'Invalid whisper storage path specified.'
            return None

        mail = self._setup_mail()
        files = self._attach_files(mail)
        return mail if (files > 0) else None

    def _setup_mail(self):
        mail = MIMEMultipart()
        mail['To'] = self.settings.EMAIL_TO
        mail['From'] = self.settings.EMAIL_FROM
        mail['Subject'] = self.settings.EMAIL_SUBJECT_VALIDATION_KEY
        mail.attach(MIMEText(self.settings.EMAIL_BODY_VALIDATION_KEY))
        return mail

    def _attach_files(self, mail):
        attached_files = 0
        print "Scanning for files.."
        # Use generator to walk storage directory
        for path in self._match_files(self.storage_dir):
            attachment = self.create_attachment(path, self._path_to_metric_filename(path))
            if attachment:
                mail.attach(attachment)
                attached_files += 1
        print "Found %d files for sending." % attached_files
        return attached_files

    def _match_files(self, path):
        c = self.settings.METRIC_PATTERNS_TO_SEND
        for possible_file in self._walk_directory(path):
            for pat in c:
                if re.match(pat, possible_file) is not None:
                    print 'Found match: ' + possible_file
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