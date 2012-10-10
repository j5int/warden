from setuptools import setup
import re

def get_version():
    VERSIONFILE="warden/__init__.py"
    initfile_lines = open(VERSIONFILE, "rt").readlines()
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    for line in initfile_lines:
        mo = re.search(VSRE, line, re.M)
        if mo:
            return mo.group(1)
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setup(name             = 'warden',
      version          = get_version(),
      license          =  'MIT',
      description      = 'A set of tools for monitoring Python applications, and shipping events to Sentry and metrics to Graphite',
      long_description = \
"""
Warden is a Python application that monitors other Python applications running locally, and ships events to a Sentry instance and metrics to a Graphite instance.

Warden can tail log files, watch that processes are running, ping an HTTP url, and track memory and CPU usage.

It provides a plug-in architecture allowing custom checks to be implemented.

Finally, there is an API that can be used by the monitored application to publish events, and do some internal checks (e.g. for stuck threads).
""",
      author           = 'Matthew Hampton',
      author_email     = 'support@sjsoft.com',
      packages         = ['warden'],
      requires         = [],
      keywords         = 'sentry carbon graphite monitoring',
      url              = 'https://github.com/matthewhampton/warden',
      classifiers      = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Environment :: Web Environment',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: System :: Monitoring',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
      ])
